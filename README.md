# internxt-syncer

A simple tool for syncing directories with the internxt cloud storage

It works as a wrapper script of the https://github.com/internxt/cli


## Simple syncer usage

Just:

    ./simple-syncer.sh up dede7b572-9213-4451-cb9a-c05a458bb702 ~/dir/to/backup

or

    ./simple-syncer.sh down dede7b572-9213-4451-cb9a-c05a458bb702 ~/dir/to/restore

If having trouble running interxt cli, set and export your own `INTERNXT_CLI` executable beforehand.
