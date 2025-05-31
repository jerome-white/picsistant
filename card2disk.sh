#!/bin/bash

export PYTHONLOGLEVEL=info
STUDIO=`mktemp --directory`

source=`mktemp --directory --tmpdir=$STUDIO`
while getopts 'a:d:s:vh' option; do
    case $option in
	a) adjust=$OPTARG ;;
        d) destination=$OPTARG ;;
        s)
	    ln --symbolic "`realpath "$OPTARG"`" $source/`uuid -v4`
	    ;;
	v) videos="--with-videos" ;;
        h)
	    cat <<EOF
Usage: $0
 -s Source
 -d Destination
 -v Also archive video
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
    | python card2disk.py $videos --destination $destination
EOF
rm --recursive --force $STUDIO
