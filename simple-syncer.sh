#!/bin/bash
# The simple internxt cloud drive synchronizer by utilising the internxt-cli tool.
# See: https://github.com/internxt/cli
# Walks recursivelly specified local system/cloud location and either fully uploads or downloads
# from/to the specified local/server location.

########################################################################################################################

# the logfile name
LOGFILE="logs.log"

# the internxt cli script executable
INTERNXT_CLI="${INTERNXT_CLI:-internxt}"

# the common flags to the cli command
COMMON_FLAGS="--non-interactive --json"

########################################################################################################################
# logging

function log() {
	local path=$1; shift
	local message=$*
	timestamp=$(date)

	echo "$timestamp $path: $message" >> $LOGFILE
	echo "$path: $message" >&2
}

function debug_log() {
	local path=$1; shift
	local message=$*
	timestamp=$(date)

	echo "$timestamp $path: $message" >> $LOGFILE
}

########################################################################################################################
# the internxt-cli wrappers and helpers

# Calls the particular internxt cli command with arguments (if enabled debug logs full command and response)
# and checks for error. Stdouts the full json server response. Returns the error code.
function exec_cli_command() {
  local path=$1; shift
  local command_name=$1; shift
  local args=("$@")

  debug_log "$path" "$INTERNXT_CLI $command_name $COMMON_FLAGS" "${args[@]}"
  response=$($INTERNXT_CLI $command_name $COMMON_FLAGS "${args[@]}")
	debug_log "$path" "$response"

  echo "$response"

  check_for_error "$path" "$response"
	error_code=$#
	return "$error_code"
}

ERROR_CODE_OTHER=100
ERROR_CODE_SESSION_EXPIRED=101
ERROR_CODE_DIRECTORY_ALREADY_EXIST=111
ERROR_CODE_FILE_ALREADY_EXIST=121
ERROR_CODE_FILE_IS_EMPTY=122

# Detects the kind of error in the code.
function detect_error_code() {
  local message=$1

  case "$message" in
    "Folder with the same name already exists in this location")
      echo $ERROR_CODE_DIRECTORY_ALREADY_EXIST
      ;;
    "File already exists")
      echo $ERROR_CODE_FILE_ALREADY_EXIST
      ;;
    "The file is empty. Uploading empty files is not allowed.")
      echo $ERROR_CODE_FILE_IS_EMPTY
      ;;
    "The session has expired, please login again")
      echo $ERROR_CODE_SESSION_EXPIRED
      ;;
    *)
      echo $ERROR_CODE_OTHER
      ;;
  esac
}

# For given response, checks whether there an error hapepned. If so, logs error/warning based on its kind.
# Returns the error code.
function check_for_error() {
  local path=$1
  local response=$2

  local success=$(echo "$response" | jq '.success' | tr -d '\"')
  if [ "$success" == "true" ] ; then
    return 0
  fi

  local message=$(echo "$response" | jq '.message' | tr -d '\"')
  local error_code=$(detect_error_code "$message")

  if [ "$error_code" == "$ERROR_CODE_DIRECTORY_ALREADY_EXIST" ] || [ "$error_code" == "$ERROR_CODE_FILE_ALREADY_EXIST" ]; then
    log "$path" "WARNING ($error_code): $message"
    return "$error_code"
  fi

  log "$path" "ERROR ($error_code): $message"

  if [ "$error_code" == "$ERROR_CODE_SESSION_EXPIRED" ] ; then
    exit "$error_code"
  fi

  return "$error_code"
}


########################################################################################################################
# hell world

response=$(exec_cli_command "." "whoami")
echo "$response" | jq ".login.user.email"
