import os
import stat
import shutil
import operator as op
import itertools
from pathlib import Path
from argparse import ArgumentParser
from datetime import datetime

import exifread

def mkfname(source, path):
    suffix = source.suffix.lower()

    for j in range(100):
        fname = '{0}-{1:02d}'.format(base, j)
        destination = path.joinpath(fname).with_suffix(suffix)
        if not destination.exists():
            return destination

    raise ValueError()

arguments = ArgumentParser()
arguments.add_argument('--source', type=Path)
arguments.add_argument('--destination', type=Path)
# arguments.add_argument('--adjust')
args = arguments.parse_args()

progress = 1
destfmt = [ '%Y', '%m-%b', '%d-%H%M%S' ]

for source in args.source.glob('**/*'):
    if source.is_dir():
        continue

    with source.open('rb') as fp:
        tags = exifread.process_file(fp, details=False, strict=True)

    key = 'Image DateTime'
    key_ = key + 'Original'
    try:
        creation = tags[key_] if key_ in tags else tags[key]
    except KeyError:
        continue

    ctime = datetime.strptime(str(creation), '%Y:%m:%d %H:%M:%S')
    (*relative, base) = [ ctime.strftime(x).upper() for x in destfmt ]
    path = args.destination.joinpath(*relative)
    destination = mkfname(source, path)

    fname = str(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(source), fname)
    os.chmod(fname, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    for (i, j) in zip(('<', '>'), (source, destination)):
        print(progress, i, str(j))

    progress += 1
