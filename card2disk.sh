#!/bin/bash

export PYTHONLOGLEVEL=info

tmp=`mktemp --directory`
while getopts 'd:s:h' option; do
    case $option in
        s)
	    while true; do
		link=$tmp/`uuid -v4`
		if [ ! -e $link ]; then
		    ln --symbolic "$OPTARG" $link
		    break
		fi
	    done
	    ;;
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
exiftool -recurse -csv -quiet $tmp | \
    python card2disk.py --destination $destination
rm --recursive --force $tmp
EOF
