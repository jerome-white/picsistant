#!/bin/bash

while getopts 'd:s:h' option; do
    case $option in
        s) source=$OPTARG ;;
        d) destination=$OPTARG ;;
        h)
	    cat <<EOF
Usage: $0
 -s Source
 -d Destination
EOF
            exit 0
            ;;
        *) echo -e Unrecognized option \"$option\" ;;
    esac
done

caffeinate -i bash <<EOF
exiftool -recurse -csv -quiet "$source" | \
    python card2disk.py --destination $destination
EOF
