#!/bin/bash
# The simple internxt cloud drive synchronizer by utilising the internxt-cli tool.
# See: https://github.com/internxt/cli
# Walks recursivelly specified local system/cloud location and either fully uploads or downloads
# from/to the specified local/server location.

########################################################################################################################

# the logfile name
LOGFILE="logs.log"

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
# hell world

log "." "hi"
