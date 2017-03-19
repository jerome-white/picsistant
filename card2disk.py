import os
import stat
import shutil
import operator as op
import itertools
from pathlib import Path
from argparse import ArgumentParser
from datetime import datetime

import exifread

def creation_time(image):
    try:
        with image.open('rb') as fp:
            tags = exifread.process_file(fp, details=False, strict=True)

            key = 'Image DateTime'
            key_ = key + 'Original'
            ctime = tags[key_] if key_ in tags else tags[key]

            return datetime.strptime(str(ctime), '%Y:%m:%d %H:%M:%S')
    except IsADirectoryError:
        pass
    except KeyError:
        pass

    raise ValueError()

def mkfname(source, destination, ctime):
    destfmt = [ '%Y', '%m-%b', '%d-%H%M%S' ]
    (*relative, base) = [ ctime.strftime(x).upper() for x in destfmt ]
    
    path = destination.joinpath(*relative)

    for j in range(100):
        fname = '{0}-{1:02d}'.format(base, j)
        output = path.joinpath(fname).with_suffix(source.suffix.lower())
        if not output.exists():
            return output

    raise ValueError()

arguments = ArgumentParser()
arguments.add_argument('--source', type=Path)
arguments.add_argument('--destination', type=Path)
# arguments.add_argument('--adjust')
args = arguments.parse_args()

picture = 1
for source in args.source.glob('**/*'):
    try:
        ctime = creation_time(source)
        output = mkfname(source, args.destination, ctime)
    except ValueError:
        continue

    destination = str(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(source), destination)
    os.chmod(destination, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    for (i, j) in zip(('<', '>'), (source, output)):
        print(picture, i, str(j))

    picture += 1
