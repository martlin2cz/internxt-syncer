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

# the location of the internxt cli drive
INTERNXT_DRIVE_URL="https://drive.internxt.com"

########################################################################################################################
# logging

LOGGING_VERBOCITY="simple" # "quiet", "simple", "verbose" or debug"

function log_to_file() {
	local message=$*
	local timestamp=$(date)

	echo "$timestamp $message" >> $LOGFILE
}

function log_to_console() {
	local args=$*

	echo $args >&2
}

function log_to_console_nobreak() {
	local args=$*

	echo -n $args >&2
}

function log_debug() {
  local path=$1; shift
	local message=$*

  if [ "$LOGGING_VERBOCITY" == "debug" ] ; then
    log_to_file "$path: $message"
  fi
}

function log_verbose() {
  local path=$1; shift
	local message=$*

if [ "$LOGGING_VERBOCITY" == "debug" ] || [ "$LOGGING_VERBOCITY" == "verbose" ]; then
    log_to_console "$path: $message"
  fi

  if [ "$LOGGING_VERBOCITY" == "debug" ] || [ "$LOGGING_VERBOCITY" == "verbose" ] || [ "$LOGGING_VERBOCITY" == "simple" ]; then
    log_to_file "$path: $message"
  fi
}

function log_simple_pre() {
	local pre_message=$*

  if [ "$LOGGING_VERBOCITY" == "simple" ]; then
    log_to_console_nobreak "$pre_message .."
  fi
}

function log_simple_post() {
	local post_message=$*

  if [ "$LOGGING_VERBOCITY" == "simple" ]; then
    log_to_console ".. $post_message"
  fi
}

function log_error_or_warning() {
    local path=$1; shift
  	local message=$*

    log_to_file "$path: $message"

    if [ "$LOGGING_VERBOCITY" == "simple" ]; then
      log_to_console "$message"
    else
      log_to_console "$path" "$message"
    fi
}
########################################################################################################################
# the internxt-cli wrappers and helpers

# Calls the particular internxt cli command with arguments (if enabled debug logs full command and response)
# and checks for error. Stdouts the full json server response. Returns the error code.
function exec_cli_command() {
  local path=$1; shift
  local command_name=$1; shift
  local args=("$@")

  log_debug "$path" "$INTERNXT_CLI $command_name $COMMON_FLAGS" "${args[@]}"
  response=$($INTERNXT_CLI $command_name $COMMON_FLAGS "${args[@]}")
	log_debug "$path" "$response"

  echo "$response"

  check_for_error "$path" "$response"
	error_code=$?
	return "$error_code"
}

ERROR_CODE_OTHER=100
ERROR_CODE_SESSION_EXPIRED=101
ERROR_CODE_DIRECTORY_ALREADY_EXIST=111
ERROR_CODE_FILE_ALREADY_EXIST=121
ERROR_CODE_FILE_IS_EMPTY=122
ERROR_CODE_NO_ID=150

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
    log_error_or_warning "$path" "WARNING ($error_code): Already exist ($message)"
    return "$error_code"
  fi

  if [ "$error_code" == "$ERROR_CODE_SESSION_EXPIRED" ] ; then
    log_error_or_warning "$path" "ERROR ($error_code): Session expired ($message)"
    return "$error_code"
  fi

  log_error_or_warning "$path" "ERROR ($error_code): $message"
  return "$error_code"
}

#########################################################################################################################
# UPLOADING

# Creates specified directory on the server. Stdouts new directory id, returns error code.
function do_create_directory() {
	local path=$1
	local owner_dir_id=$2

	local name="$(basename "$path")"
	log_verbose "$path" "CREATING DIRECTORY $name ON SERVER into $owner_dir_id directory ..."

  local response
	response=$(exec_cli_command "$path" create-folder --id "$owner_dir_id" --name "$name")

	local error_code=$?
	if [ $error_code != 0 ] ; then
	  # error/warning already logged
	  return $error_code
	fi

	local id=$(echo "$response" | jq '.folder.uuid' | tr -d '\"')

	if [ -z "$id"  ] || [ "$id" == "null" ] ; then
		log_verbose "$path" "ERROR ($ERROR_CODE_NO_ID): Did not recieve the server directory id."
		return $ERROR_CODE_NO_ID
  fi

  log_verbose "$path" "CREATED DIRECTORY $name ON SERVER with id $id!"
  echo "$id"
  return 0
}

function do_upload_file() {
	local path=$1
	local owner_dir_id=$2

	local name="$(basename "$path")"
	log_verbose "$path" "UPLOADING FILE $name TO SERVER into $owner_dir_id directory ..."

  local response
	response=$(exec_cli_command "$path" upload-file --destination "$owner_dir_id" --file "$path")

	local error_code=$?
	if [ $error_code != 0 ] ; then
	  # error/warning already logged
	  return $error_code
	fi

	local id=$(echo "$response" | jq '.file.uuid' | tr -d '\"')

	if [ -z "$id"  ] || [ "$id" == "null" ] ; then
		log_verbose "$path" "ERROR ($ERROR_CODE_NO_ID): Did ton recieve the server file id."
		return $ERROR_CODE_NO_ID
  fi

  log_verbose "$path" "UPLOADED FILE $name TO SERVER with id $id!"
  echo "$id"
  return 0
}

# Walks recursivelly the local directory tree and uploads its contents to the specified server directory.
# Recursive. Echoes the processed directory id, returns 0 if succeeds at bit or ERROR_CODE_NO_ID if fails totally.
function upload_directory_recursivelly() {
	local dir_path=$1
	local owner_dir_id=$2

	local dir_name=$(basename "$dir_path")
	log_verbose "$dir_path" "PROCESSING DIRECTORY $dir_name to upload as child of $owner_dir_id ..."

	local dir_id=$(do_create_directory "$dir_path" "$owner_dir_id")
  if [ -z "$dir_id" ] ; then
    log_verbose "$dir_path" "Cannot upload because I don't know the server id of the directory. Skipping."
    return $ERROR_CODE_NO_ID
  fi

	find "$dir_path" -mindepth 1 -maxdepth 1 | while read resource_path ; do
		log_debug "$resource_path" "PROCESSING CHILD ELEMENT $resource_path ..."

		local server_id=""
		if [ -d "$resource_path" ] ; then
		  log_simple_pre "$resource_path"
		  log_simple_post ":"

			server_id=$(upload_directory_recursivelly "$resource_path" "$dir_id")

			log_simple_pre "$resource_path"
			log_simple_post "$server_id"
		else
		  log_simple_pre "$resource_path"
			server_id=$(do_upload_file "$resource_path" "$dir_id")
      log_simple_post "$server_id"
		fi

		log_debug "$resource_path" "PROCESSED CHILD ELEMENT $resource_path (got server id $server_id)"
	done

	log_verbose "$dir_path" "PROCESSED DIRECTORY $owner_dir_id!"
	echo "$dir_id"
	return 0
}


#########################################################################################################################
# DOWNLOADING

# Downloads the specified file. Echoes its path (if suceeded), returns error code.
function do_download_file() {
  local file_id=$1
  local owner_dir_path=$2
  local file_info=$3

  local base_file_name=$(echo "$file_info" | jq ".plainName" | tr -d '\"')

  local file_name=""
  if [ -z "$file_type" ] || [ "$file_type" == "null" ] ; then
    file_name="$base_file_name"
  else
    file_name="$base_file_name.$file_type"
  fi

  local file_path="$owner_dir_path/$file_name"
  log_verbose "$file_path" "DOWNLOADING SERVER FILE $file_id as $file_name into $owner_dir_path ..."

  local response
  response=$(exec_cli_command "$file_path" download-file "--id=$file_id" "--directory=$owner_dir_path" "--overwrite")

	local error_code=$?
	if [ $error_code != 0 ] ; then
	  # error/warning already logged
	  return $error_code
	fi

  echo "$file_path"
  log_verbose "$file_path" "DOWNLOADED SERVER FILE $file_id as $file_name ..."
  return 0
}

# "Downloads" (creates new local directory) the specified directory. Echoes its path, returns error code.
function do_download_directory() {
  local dir_id=$1
  local owner_dir_path=$2
  local dir_info=$3

  local dir_name=$(echo "$dir_info" | jq ".plainName" | tr -d '\"')
  local dir_path="$owner_dir_path/$dir_name"

  log_verbose "$dir_path" "CREATING $dir_name for server $dir_id ..."

  mkdir "$dir_path"

	local error_code=$?
	if [ $error_code != 0 ] ; then
	  log_error_or_warning "$dir_path" "ERROR (mkdir: $error_code): Directory creation failed."
	fi

  echo "$dir_path"
  log_verbose "$dir_path" "CREATED DIRECTORY $dir_name as $dir_path!"
}

# Walks recursivelly the server directory structure and downloads all files and directories inside.
# Echoes the nothing, returns 0 if some sucess or error code if unable to fetch directory contents.
function download_directory_recursivelly() {
  local dir_path=$1
	local dir_id=$2

  log_verbose "$dir_path" "Downloading contents of server directory $dir_id into $dir_path ..."
  local directory_contents_response
  directory_contents_response=$(exec_cli_command "$dir_path" list --id "$dir_id")
  local error_code=$?

	if [ $error_code != 0 ] ; then
    log_verbose "$dir_path" "Cannot download because I don't know contents of the directory. Skipping."
	  return $error_code
	fi

  child_files_ids=$(echo "$directory_contents_response" | jq ".list.files[].uuid" | tr -d '\"')
  for child_file_id in $child_files_ids; do
      log_debug "$dir_path/???" "PROCESSING CHILD FILE $child_file_id ..."

      file_info=$(echo "$directory_contents_response" | jq ".list.files[] | select(.uuid==\"$child_file_id\")")
      local child_file_path=$(do_download_file "$child_file_id" "$dir_path" "$file_info")

      log_debug "$dir_path/???" "PROCESSED CHILD FILE $child_file_id as $child_file_path!"
  done

  local child_dirs_ids=$(echo "$directory_contents_response" | jq ".list.folders[].uuid" | tr -d '\"')
  for child_dir_id in $child_dirs_ids; do
    log_debug "$dir_path/???" "PROCESSING CHILD DIRECTORY $child_dir_id ..."

    local dir_info=$(echo "$directory_contents_response" | jq ".list.folders[] | select(.uuid==\"$child_dir_id\")")
    local child_dir_path=$(do_download_directory "$child_dir_id" "$dir_path" "$dir_info")

    download_directory_recursivelly "$child_dir_path" "$child_dir_id"
    log_debug "$dir_path/???" "PROCESSED CHILD DIRECTORY $child_dir_id as $child_dir_path!"
  done

  log_verbose "$dir_path" "Downloaded contents of the $dir_id directory!"
}


########################################################################################################################
# command line arguments processing

# usage
if [ "$#" -lt "3" ] || [ "$0" == "-h" ] || [ "$0" == "--help" ] ; then
	echo "Usage: $0 [--debug|-D | --verbose|-V | --quiet|-Q] up|down ROOT_DIR_SERVER_ID ROOT_DIR_LOCAL_PATH"
	echo "(please keep this order)"
	echo "for example $0 -debug up '3454-332d-34ad-444b' ~/stuff/something"
	exit
fi

# logging level
case $1 in
  "--debug" | "-D")
    LOGGING_VERBOCITY="debug"
    shift
  ;;
  "--verbose" | "-V")
    LOGGING_VERBOCITY="verbose"
    shift
  ;;
  "--quiet" | "-Q")
    LOGGING_VERBOCITY="quiet"
    shift
  ;;
esac

# actual arguments
ACTION=$1
ROOT_DIR_SERVER_ID=$2
ROOT_DIR_LOCAL_PATH=$3

# validation of theese
if ! [[ "$ROOT_DIR_SERVER_ID" =~ ^([0-9a-f]{4,}\-){4,}([0-9a-f]{4,})$ ]] ; then
  echo "$ROOT_DIR_SERVER_ID doesn't seem to be valid server uuid." >&2
	exit 11
fi

if [ ! -d "$ROOT_DIR_LOCAL_PATH" ] ; then
	echo "$ROOT_DIR_LOCAL_PATH directory doesn't exist." >&2
	exit 12
fi

# actually executing the action
case $ACTION in
  up|upload)
    dir_id=$(upload_directory_recursivelly "$ROOT_DIR_LOCAL_PATH" "$ROOT_DIR_SERVER_ID")
    error_code=$?
    if [ "$error_code" == 0 ] ; then
      echo "Upload completed, see ${INTERNXT_DRIVE_URL}/folder/$dir_id"
    else
      echo "Upload failed or incomplete."
      exit 21
    fi

    ;;
  down|download)
    download_directory_recursivelly "$ROOT_DIR_LOCAL_PATH" "$ROOT_DIR_SERVER_ID"
    error_code=$?
    if [ "$error_code" == 0 ] ; then
      echo "Download completed, see $ROOT_DIR_LOCAL_PATH"
    else
      echo "Download failed or incomplete."
      exit 22
    fi
    ;;
  *)
  echo "Unknown action $ACTION. Use either 'up/upload' or 'down/download'" >&2
	exit 13
	;;
esac

########################################################################################################################
