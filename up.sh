#!/bion/bash

#INTERNXT_CLI="echo internext-cli"
INTERNXT_CLI="node $HOME/apps/nodejs/nodejs-v22-15.0-linux-x64/node-v22.15.0-linux-x64/lib/node_modules/@internxt/cli/bin/run.js"
COMMON_FLAGS="--non-interactive --json"
MAPPING_DB_FILE=mapping.db
ERRORS_FILE=errors.json.txt

initialise() {
	local root_dir_id=$1
	local root_dir_path=$2

	echo "Initialising mapping database with root dir id $root_dir_id ..." >&2
	sqlite3 $MAPPING_DB_FILE "CREATE TABLE directories (id, path, name)"

	root_parent_path="$(dirname "$root_dir_path")/"
	record_new_directory "$root_parent_path" "" "$root_dir_id"

}

function get_id_of_dir() {
	local path=$1

	sqlite3 $MAPPING_DB_FILE "SELECT id FROM directories WHERE path = '$path' LIMIT 1"
}

function record_new_directory() {
	local path=$1
	local name=$2
	local id=$3

	sqlite3 $MAPPING_DB_FILE  "INSERT INTO directories (id, path, name) VALUES ('$id', '$path', '$name')"
}

function create_directory() {
	local path=$1
	echo "Creating directory $path ..." >&2

	parent_path="$(dirname "$path")/"
	name="$(basename "$path")"

	parent_dir_id=$(get_id_of_dir $parent_path)
	if [ "$parent_dir_id" == "" ] ; then
		echo "No record of parent directory $parent_path" >&2
		echo "$path" >> $ERRORS_FILE
		echo "$parent_path" >> "$ERRORS_FILE"
		exit 1
	fi
		
	response=$($INTERNXT_CLI create-folder $COMMON_FLAGS --id=$parent_dir_id --name $name)
	id=$(echo "$response" | jq '.folder.uuid' | tr -d '\"')

	if [ "$id" == "" ] ; then
		echo "Directory $path creation failed!" >&2
		echo "$path" >> $ERRORS_FILE
		echo "$response" >> $ERRORS_FILE
		exit 2
	else
		record_new_directory "$path" "$name" "$id"
	fi
}

function upload_file() {
	local path=$1
	echo "Uploading file $path ..." >&2

	parent_path="$(dirname "$path")/"
	name="$(basename "$path")"

	parent_dir_id=$(get_id_of_dir $parent_path)
	if [ "$parent_dir_id" == "" ] ; then
		echo "No record of parent directory $parent_path" >&2
		echo "$path" >> $ERRORS_FILE
		echo "$parent_path" >> "$ERRORS_FILE"
		exit 1
	fi
		
	response=$($INTERNXT_CLI upload-file $COMMON_FLAGS --destination=$parent_dir_id --file $path)
	id=$(echo "$response" | jq '.file.uuid' | tr -d '\"')

	if [ "$id" == "" ] ; then
		echo "File $path upload failed!" >&2
		echo "$path" >> $ERRORS_FILE
		echo "$response" >> $ERRORS_FILE
		exit 2
	fi
}

function upload_whole() {
	local root_dir_path=$1

	echo "Starting to process $roo_dir_path" >&2
	find "$root_dir_path" | while read resource_path ; do
		echo "Processing $resource_path" >&2

		if [ -d "$resource_path" ] ; then
			dir_path=$(echo "$resource_path/" | sed 's|//|/|')
			create_directory "$dir_path"
		else
			upload_file "$resource_path"
		fi
	done
	echo "Finished processing $root_dir_path" >2
}

if [ "$#" != "2" ] ; then 
	echo "Usage: $0 [TARGET_DIR_ID] [SOURCE_DIR_PATH]"
	echo "for example $0i '3454-332d-33ad-444b' ~/stuff/something" 
	exit 
fi

ROOT_DIR_ID=$1
ROOT_DIR_PATH=$2

#set -x
initialise $1 $2

upload_whole $ROOT_DIR_PATH
#create_dir "$ROOT_DIR_PATH"
#create_dir "foo/bar"
#set +x



