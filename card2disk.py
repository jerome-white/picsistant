import os
import stat
import shutil
import operator as op
from pathlib import Path
from argparse import ArgumentParser
from datetime import datetime
from itertools import filterfalse
from multiprocessing import Pool

import exifread

def mkfname(source, path, prefix):
    suffix = source.suffix.lower()

    for j in range(100):
        fname = '{0}-{1:02d}'.format(prefix, j)
        destination = path.joinpath(fname).with_suffix(suffix)
        if not destination.exists():
            return destination

    raise ValueError()

def func(args):
    (source, destination) = args

    with source.open('rb') as fp:
        tags = exifread.process_file(fp, details=False, strict=True)

    key = 'Image DateTime'
    key_ = key + 'Original'
    try:
        creation = tags[key_] if key_ in tags else tags[key]
    except KeyError:
        return

    destfmt = [ '%Y', '%m-%b', '%d-%H%M%S' ]
    ctime = datetime.strptime(str(creation), '%Y:%m:%d %H:%M:%S')
    (*relative, base) = [ ctime.strftime(x).upper() for x in destfmt ]

    path = destination.joinpath(*relative)
    try:
        target = mkfname(source, path, base)
    except ValueError:
        return
    target.parent.mkdir(parents=True, exist_ok=True)

    fname = str(target)
    shutil.copy2(str(source), fname)
    os.chmod(fname, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    return (source, target)

arguments = ArgumentParser()
arguments.add_argument('--source', type=Path)
arguments.add_argument('--destination', type=Path)
# arguments.add_argument('--adjust')
args = arguments.parse_args()

with Pool() as pool:
    each = filterfalse(op.methodcaller('is_dir'), args.source.glob('**/*'))
    iterable = map(lambda x: (x, args.destination), each)

    for (i, j) in enumerate(filter(None, pool.imap_unordered(func, iterable))):
        for (x, y) in zip(('<', '>'), j):
            print(i, x, str(y))
