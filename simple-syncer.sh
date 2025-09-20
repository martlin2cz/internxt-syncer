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
    log "$path" "WARNING ($error_code): $message"
    return "$error_code"
  fi

  log "$path" "ERROR ($error_code): $message"

  if [ "$error_code" == "$ERROR_CODE_SESSION_EXPIRED" ] ; then
    exit "$error_code"
  fi

  return "$error_code"
}

#########################################################################################################################
# UPLOADING

# Creates specified directory on the server. Stdouts new directory id, returns error code.
function do_create_directory() {
	local path=$1
	local owner_dir_id=$2

	local name="$(basename "$path")"
	log "$path" "CREATING DIRECTORY $name in $owner_dir_id ..."

	local response=$(exec_cli_command "$path" create-folder --id "$owner_dir_id" --name "$name")
	local error_code=$?
	if [ $error_code != 0 ] ; then
	  return $error_code
	fi

	local id=$(echo "$response" | jq '.folder.uuid' | tr -d '\"')

	if [ -z "$id"  ] || [ "$id" == "null" ] ; then
		log "$path" "ERROR ($ERROR_CODE_NO_ID): NO ID recieved for DIRECTORY!"
		return $ERROR_CODE_NO_ID
	else
		log "$path" "CREATED DIRECTORY with id $id!"
		echo "$id"
		return 0
	fi
}

function do_upload_file() {
	local path=$1
	local owner_dir_id=$2

	local name="$(basename "$path")"
	log "$path" "UPLOADING FILE $name into $owner_dir_id ..."

	local response=$(exec_cli_command "$path" upload-file --destination "$owner_dir_id" --file "$path")
	local error_code=$?
	if [ $error_code != 0 ] ; then
	  return $error_code
	fi

	local id=$(echo "$response" | jq '.file.uuid' | tr -d '\"')

	if [ -z "$id"  ] || [ "$id" == "null" ] ; then
		log "$path" "ERROR ($ERROR_CODE_NO_ID): NO ID recieved for FILE!"
		return $ERROR_CODE_NO_ID
	else
		log "$path" "UPLOADED FILE with id $id!"
		echo "$id"
		return 0
	fi
}

# Walks recursivelly the local directory tree and uploads its contents to the specified server directory.
# Recursive. Echoes the processed directory id, returns 0 if succeeds at bit or ERROR_CODE_NO_ID if fails totally.
function upload_directory_recursivelly() {
	local dir_path=$1
	local owner_dir_id=$2

	local dir_name=$(basename "$dir_path")
	log "$dir_path" "Uploading directory $dir_path as child of server dir $owner_dir_id ..."

	local dir_id=$(do_create_directory "$dir_path" "$owner_dir_id")
  if [ -z "$dir_id" ] ; then
    log "$dir_path" "Cannot upload because I don't know the server id. Skipping."
    return $ERROR_CODE_NO_ID
  fi

	find "$dir_path" -mindepth 1 -maxdepth 1 | while read resource_path ; do
		debug_log "$resource_path" "processing ..."

		local server_id=""
		if [ -d "$resource_path" ] ; then
			server_id=$(upload_directory_recursivelly "$resource_path" "$dir_id")
		else
			server_id=$(do_upload_file "$resource_path" "$dir_id")
		fi

		debug_log "$resource_path" "processed (recieved id $server_id)!"
	done

	log "$dir_path" "Uploaded directory into $owner_dir_id!"
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

  debug_log "$owner_dir_path/???" "downloading server file $file_log"
  local base_file_name=$(echo "$file_info" | jq ".plainName" | tr -d '\"')
  local file_type=$(echo "$file_info" | jq ".type" | tr -d '\"')

  local file_name=""
  if [ -z "$file_type" ] || [ "$file_type" == "null" ] ; then
    file_name="$base_file_name"
  else
    file_name="$base_file_name.$file_type"
  fi

  local file_path="$owner_dir_path/$file_name"
  log "$file_path" "DOWNLOADING FILE $file_name for $file_id ..."

  local response=$(exec_cli_command "$file_path" download-file "--id=$file_id" "--directory=$owner_dir_path" "--overwrite")
  local error_code=$?
	if [ $error_code != 0 ] ; then
	  return $error_code
	fi

  echo "$file_path"
  log "$file_path" "DOWNLOADED FILE!"
  return 0
}

# "Downloads" (creates new local directory) the specified directory. Echoes its path, returns error code.
function do_download_directory_recursivelly() {
  local dir_id=$1
  local owner_dir_path=$2
  local dir_info=$3

  debug_log "$owner_dir_path/???" "downloading server directory $dir_log"

  local dir_name=$(echo "$dir_info" | jq ".plainName" | tr -d '\"')
  local dir_path="$owner_dir_path/$dir_name"

  log "$dir_path" "CREATING $dir_name for $dir_id ..."

  mkdir "$dir_path"
  local error_code=$?
	if [ $error_code != 0 ] ; then
	  return $error_code
	fi

  echo "$dir_path"
  log "$dir_path" "CREATED DIRECTORY!"
}

# Walks recursivelly the server directory structure and downloads all files and directories inside.
# Echoes the nothing, returns 0 if some sucess or error code if unable to fetch directory contents.
function download_directory_recursivelly() {
  local dir_path=$1
	local dir_id=$2

  log "$dir_path" "Downloading contents of server directory $dir_id into $dir_path ..."
  local directory_contents_response=$(exec_cli_command "$dir_path" list --id "$dir_id")
  local error_code=$?
	if [ $error_code != 0 ] ; then
    log "$dir_path" "Cannot upload because I don't know contents of the directory. Skipping."
	  return $error_code
	fi

  child_files_ids=$(echo "$directory_contents_response" | jq ".list.files[].uuid" | tr -d '\"')
  for child_file_id in $child_files_ids; do
      file_info=$(echo "$directory_contents_response" | jq ".list.files[] | select(.uuid==\"$child_file_id\")")
      local x_file_id=$(do_download_file "$child_file_id" "$dir_path" "$file_info")
  done

  local child_dirs_ids=$(echo "$directory_contents_response" | jq ".list.folders[].uuid" | tr -d '\"')
  for child_dir_id in $child_dirs_ids; do
    local dir_info=$(echo "$directory_contents_response" | jq ".list.folders[] | select(.uuid==\"$child_dir_id\")")
    local child_dir_path=$(do_download_directory_recursivelly "$child_dir_id" "$dir_path" "$dir_info")

    download_directory_recursivelly "$child_dir_path" "$child_dir_id"
  done

  log "$dir_path" "Downloaded contents!"
}


########################################################################################################################
# command line arguments processing

if [ "$#" != "2" ] || [ "$0" == "-h" ] || [ "$0" == "--help" ] ; then
	echo "Usage: $0 [ROOT_DIR_SERVER_ID] [ROOT_DIR_LOCAL_PATH]"
	echo "for example $0 '3454-332d-34ad-444b' ~/stuff/something"
	exit
fi

ROOT_DIR_SERVER_ID=$1
ROOT_DIR_LOCAL_PATH=$2

if ! [[ "$ROOT_DIR_SERVER_ID" =~ ^([0-9a-f]{4,}\-){4,}([0-9a-f]{4,})$ ]] ; then
  echo "$ROOT_DIR_SERVER_ID doesn't seem to be valid server uuid." >&2
	exit 11
fi

if [ ! -d "$ROOT_DIR_LOCAL_PATH" ] ; then
	echo "$ROOT_DIR_LOCAL_PATH directory doesn't exist." >&2
	exit 12
fi

download_directory_recursivelly "$ROOT_DIR_LOCAL_PATH" "$ROOT_DIR_SERVER_ID"
echo "Download completed, see $ROOT_DIR_LOCAL_PATH"

########################################################################################################################
