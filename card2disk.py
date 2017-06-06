import os
import sys
import stat
import shutil
import operator as op
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser
from multiprocessing import Pool

import exifread

class Result:
    def __init__(self, source, target=None):
        self.source = source
        self.target = target

    def __bool__(self):
        return self.target is not None

    def __str__(self):
        return self.source.stem + ' -> ' + str(self.target) if self else ''

def func(args):
    (source, destination) = args

    #
    # Read exif information
    #
    with source.open('rb') as fp:
        tags = exifread.process_file(fp, details=False, strict=True)

    #
    # Extract the time at which the picture was taken
    #
    key = 'Image DateTime Original'
    while key.find(' ') > 0:
        if key in tags:
            creation = tags[key]
            break
        pieces = key.split()
        key = ' '.join(pieces[:-1])
    else:
        return Result(source)

    destfmt = [ '%Y', '%m-%b', '%d-%H%M%S' ]
    ctime = datetime.strptime(str(creation), '%Y:%m:%d %H:%M:%S')
    (*relative, base) = [ ctime.strftime(x).upper() for x in destfmt ]

    #
    # Use the time to create a destination file name
    #
    path = destination.joinpath(*relative)
    suffix = source.suffix.lower()
    for i in range(100):
        fname = '{0}-{1:02d}'.format(base, i)
        target = path.joinpath(fname).with_suffix(suffix)
        if not target.exists():
            break
    else:
        return Result(source)

    (src, dst) = map(str, (source, target))

    #
    # Disk access!
    #
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    os.chmod(dst, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    return Result(source, target)

arguments = ArgumentParser()
arguments.add_argument('--source', type=Path)
arguments.add_argument('--destination', type=Path)
# arguments.add_argument('--adjust')
args = arguments.parse_args()

with Pool() as pool:
    each = filter(op.methodcaller('is_file'), args.source.glob('**/*'))
    iterable = map(lambda x: (x, args.destination), each)

    for (i, result) in enumerate(pool.imap_unordered(func, iterable)):
        if not result:
            print('Error:', result.source, file=sys.stderr)
        else:
            print(i, result)
