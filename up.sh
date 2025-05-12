#!/bion/bash


#ROOT_DIR_ID=TODO
INTERNXT_CLI="node $HOME/apps/nodejs/nodejs-v22-15.0-linux-x64/node-v22.15.0-linux-x64/lib/node_modules/@internxt/cli/bin/run.js"
COMMON_FLAGS="--non-interactive --json"
MAPPING_DB_FILE=mapping.db
ERRORS_FILE=errors.json.txt

initialise() {
	echo "Initialising mapping database ..." >&2
	sqlite3 $MAPPING_DB_FILE "CREATE TABLE directories (id, path, name)"
}

function get_id_of_dir() {
	local path=$1

	sqlite3 $MAPPING_DB_FILE "SELECT id FROM directories WHERE path = '$path'"
}

function record_new_directory() {
	local path=$1
	local name=$2
	local id=$3

	sqlite3 $MAPPING_DB_FILE  "INSERT INTO directories (id, path, name) VALUES ('$id', '$path', '$name')"
}

function create_dir() {
	local path=$1
	echo "Creating directory $path ..." >&2

	parent_path="$(dirname "$path")"
	name="$(basename "$path")"

#	parent_dir_id=$(get_id_of_dir $parent_path)

	response=$($INTERNXT_CLI create-folder $COMMON_FLAGS --id=$parent_dir_id --name $name)
	id=$(echo "$response" | jq '.folder.uuid' | tr -d '\"')

	if [ "$id" == "" ] ; then
		echo "Directory $path creation failed!" >&2
		echo $path >> $ERRORS_FILE
		echo $response >> $ERRORS_FILE
		exit 1
	else
		record_new_directory "$path" "$name" "$id"
	fi

}

initialise

set -x
create_dir "foo/bar-3"
set +x



