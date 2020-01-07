import os
import sys
import csv
import stat
import shutil
from string import Template
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser
from multiprocessing import Pool, JoinableQueue

def exif2path(exif, suffix):
    #
    # Extract the time at which the picture was taken
    #
    keys = (
        'CreateDate',
        'DateTimeOriginal',
        'ModifyDate',
    )

    for i in filter(lambda x: x in exif, keys):
        creation = exif[i]
        break
    else:
        raise ValueError('Cannot establish creation time')

    #
    # Use the time to build a filename
    #
    ctime = (datetime
             .strptime(creation, '%Y:%m:%d %H:%M:%S')
             .strftime('%Y/%m-%b/%d-%H%M%S'))

    return Path(ctime.upper()).with_suffix(suffix.lower())

#
# Use the time to create a destination file name
#
def path2fname(path, destination, maxtries):
    tstring = '{}-$version{}'.format(path.parent.joinpath(path.stem),
                                     path.suffix.lower())
    template = Template(tstring)

    for i in range(maxtries):
        version = '{:02d}'.format(i)
        fname = template.substitute(version=version)
        target = destination.joinpath(fname)
        if not target.exists():
            return target

    raise ValueError('Cannot create unique filename')

def func(queue, destination, maxtries):
    while True:
        exif = queue.get()
        source = Path(exif['SourceFile'])

        try:
            path = exif2path(exif, source.suffix.lower())
            target = path2fname(path, destination, maxtries)
            (src, dst) = map(str, (source, target))

            #
            # Disk access!
            #
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            os.chmod(dst, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

            print(source.stem, '->', target)
        except ValueError as err:
            print('Error:', source, err, file=sys.stderr)

        queue.task_done()

arguments = ArgumentParser()
arguments.add_argument('--destination', type=Path)
arguments.add_argument('--maxtries', type=int, default=100)
arguments.add_argument('--workers', type=int)
# arguments.add_argument('--adjust')
args = arguments.parse_args()

queue = JoinableQueue()
initargs = (
    queue,
    args.destination,
    args.maxtries,
)

with Pool(args.workers, func, initargs):
    reader = csv.DictReader(sys.stdin)
    for row in reader:
        queue.put(row)
    queue.join()
