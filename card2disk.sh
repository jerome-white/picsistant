#!/bin/bash

PADDING=2
EXT=(
    jpg
    nef
)

file2name() {
    a=( `exiftool -DateTimeOriginal $1 | cut --delimiter=':' --fields=2-` )
    if [ ${#a[@]} -gt 0 ]; then
	b=`echo ${a[0]} | sed -e's/:/\//g'`
	date +%Y/%m-%b/%d-%H%M%S --date="$b ${a[1]}" | \
	    tr "[:lower:]" "[:upper:]"
    fi

    return
}

exif2touch() {
    # a=`exiftool -DateTimeOriginal $1 | sed -e's/[^0-9]//g'`
    # echo ${a:0:12}.${a:12}
    fp=( `echo $1 | cut --delimiter='/' --fields=1- --output-delimiter=' '` )
    fp=( ${fp[@]:(-3)} )

    mmddhrmm=`echo ${fp[@]:1} | \
	sed -e's/-/ /g' | \
	cut --delimiter=' ' --fields=1,3-4 --output-delimiter=''`
    echo ${fp[0]}${mmddhrmm:0:8}.${mmddhrmm:(-2)}

    return
}

format_version() {
    printf "%.${PADDING}d" $1

    return
}

extract_version() {
    echo `basename $1` | \
	cut --delimiter='-' --fields=3 | \
	cut --delimiter='.' --fields=1

    return
}

logecho() {
    if [ $verbose ]; then
	echo $@
    fi

    return
}

usage() {
    cat<<EOF
Usage: $0 [args]
  -v     Verbose
  -a arg Adjust picture timestamp: [+|-]=[H:MM]
         This argument is passed directly to exiftool's -AllDates
         option; remember to quote! See the exiftool manpage.
  -s arg Source directory (copy from)
  -d arg Destination directory (copy to). Default $DEST
  -r     Dry run (-v engaged)
  -h     Help
EOF

    return
}

dest=$DEST
while getopts 'a:d:hs:rv' option; do
    case $option in
	a) adjust=$OPTARG ;;
	v) verbose=1 ;;
        s) source=$OPTARG ;;
	d) dest=$OPTARG ;;
	r)
	    exe=echo
	    verbose=1
	    ;;
        h)
            usage
            exit 0
            ;;
        *) echo -e Unrecognized option \"$option\" ;;
    esac
done

if [ ! -w $dest ]; then
    echo "Error: Cannot write to destination \"$dest\""
    exit 1
fi

unset scratch
for e in ${EXT[@]}; do
    for i in `find "$source" -iname "*.$e"`; do
	bad=( ${bad[@]} $i )
	ver=`format_version`
	err=FAILURE

	if [ -n "$adjust" ]; then
	    if [ ! $scratch ]; then
		scratch=`mktemp --directory`
	    fi
	    file=`mktemp --tmpdir=$scratch`
	    cmd=mv
	    cp $i $file || exit 1
	    exiftool -overwrite_original_in_place -AllDates"${adjust}" $file \
		> /dev/null
	else
	    file=$i
	    cmd=cp
	fi

	fname=`file2name $file`
	if [ ! $fname ]; then
	    echo "BADEXIF: $file" >&2
	    continue
	fi

	if [ -e $dest ]; then # does this file exist already?
	    exst=( $(find $dest -name "`basename ${fname}`*.$e" 2> /dev/null) )
	    for j in ${exst[@]}; do
		diff --brief $file $j &> /dev/null
		if [ $? -eq 0 ]; then # The files are the same!
		    echo "EXISTS: $file and $j" >&2
		    continue 2
		fi

		tmp=`extract_version $j`
		if [ $tmp -ge $ver ]; then
		    ver=`format_version $(expr $tmp + 1)`
		fi
	    done
	fi

	fpath=$dest/${fname}-${ver}.$e
	mkdir --parents `dirname $fpath`
	$exe $cmd $file $fpath && {
	    if [ ! $exe ]; then
		touch -t `exif2touch $fname` $fpath
		chmod 444 $fpath
	    fi
	    err=SUCCESS
	}
	logecho $err "$file -> $fpath"

	unset bad[${#bad[@]}-1]
    done
done

if [ ${#bad[@]} -gt 0 ]; then
    echo "Unsuccessful:"
    for i in ${bad[@]}; do
	echo -e "\t$i"
    done
fi

if [ $scratch ]; then
    rm --force --recursive $scratch
fi
