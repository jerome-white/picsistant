#!/bin/bash

export PYTHONLOGLEVEL=info
STUDIO=`mktemp --directory`

source=`mktemp --directory --tmpdir=$STUDIO`
while getopts 'a:d:s:h' option; do
    case $option in
	a) adjust=$OPTARG ;;
        d) destination=$OPTARG ;;
        s)
	    ln --symbolic "`realpath "$OPTARG"`" $source/`uuid -v4`
	    ;;
        h)
	    cat <<EOF
Usage: $0
 -s Source
 -d Destination
 -a Adjust picture timestamp: [+|-]=[H:MM]
    This argument is passed directly to exiftool's -AllDates
    option; remember to quote! See the exiftool manpage.
EOF
            exit 0
            ;;
        *)
	    echo -e Unrecognized option \"$option\"
	    exit 1
	    ;;
    esac
done

if [ -n "$adjust" ]; then
    tmp=`mktemp --directory --tmpdir=$STUDIO`
    exiftool -recurse -AllDates"${adjust}" -out $tmp $source
    source=$tmp
fi

caffeinate -i bash <<EOF
exiftool -recurse -csv -quiet $source \
    | python card2disk.py --destination $destination
rm --recursive --force $STUDIO
EOF
