import os
import sys
import csv
import stat
import shutil
import logging
import itertools as it
from string import Template
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser
from multiprocessing import Pool, Lock, JoinableQueue

#
# Setup logger
#
lvl = os.environ.get('PYTHONLOGLEVEL', 'warning').upper()
fmt = '[ %(asctime)s %(levelname)s %(process)d ] %(message)s'
logging.basicConfig(format=fmt, datefmt="%H:%M:%S", level=lvl)
logging.captureWarnings(True)

#
#
#
class ExifPath:
    _keys = (
        'CreateDate',
        'DateTimeOriginal',
        'ModifyDate',
    )

    def __init__(self, with_videos):
        self.support = set([
            'image',
        ])
        if with_videos:
            self.support.add('video')

    def __call__(self, exif, suffix):
        #
        # Make sure the file type is supported
        #
        (mime, _) = exif['MIMEType'].split('/', maxsplit=1)
        if mime.casefold() not in self.support:
            raise TypeError(f'Unsupported file type "{mime}"')

        #
        # Extract the time at which the picture was taken
        #
        for i in filter(lambda x: x in exif, self._keys):
            creation = exif[i]
            break
        else:
            raise ValueError('Cannot establish creation time')

        #
        # Use the time to build a filename
        #
        ctime = (datetime
                 .strptime(creation, '%Y:%m:%d %H:%M:%S')
                 .strftime('%Y/%m-%b/%d-%H%M%S')
                 .upper())
        path = Path(ctime)

        return path.with_suffix(suffix)

#
# Use the time to create a destination file name
#
class PathName:
    def __init__(self, destination, lock, maxtries=None):
        self.destination = destination
        self.lock = lock
        self.maxtries = float('inf') if maxtries is None else maxtries

    def __call__(self, path):
        basename = path.parent.joinpath(path.stem)
        tstring = '{}-$version{}'.format(basename, path.suffix)
        template = Template(tstring)

        self.lock.acquire()
        try:
            for i in it.count():
                if i > self.maxtries:
                    raise FileExistsError('Cannot create unique filename')
                version = '{:02d}'.format(i)
                fname = template.substitute(version=version)
                target = self.destination.joinpath(fname)
                if not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.touch()
                    return target
        finally:
            self.lock.release()

def func(queue, lock, args):
    exif2path = ExifPath(args.with_videos)
    path2fname = PathName(args.destination, lock, args.maxtries)

    while True:
        exif = queue.get()
        source = Path(exif['SourceFile'])

        try:
            path = exif2path(exif, source.suffix.lower())
            target = path2fname(path)
            (src, dst) = map(str, (source, target))
            shutil.copy2(src, dst)
            os.chmod(dst, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            logging.info('{} -> {}'.format(source.name, target))
        except (TypeError, ValueError, FileExistsError) as err:
            logging.error('{} {}'.format(source, err))
        finally:
            queue.task_done()

if __name__ == '__main__':
    arguments = ArgumentParser()
    arguments.add_argument('--destination', type=Path)
    arguments.add_argument('--maxtries', type=int)
    arguments.add_argument('--with-videos', action='store_true')
    # arguments.add_argument('--adjust')
    arguments.add_argument('--workers', type=int)
    args = arguments.parse_args()

    queue = JoinableQueue()
    initargs = (
        queue,
        Lock(),
        args,
    )

    with Pool(args.workers, func, initargs):
        reader = csv.DictReader(sys.stdin)
        for row in reader:
            queue.put(row)
        queue.join()
