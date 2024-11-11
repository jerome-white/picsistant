import os
import sys
import csv
import math
import stat
import shutil
import logging
import itertools as it
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
    _exif_dt = '%Y:%m:%d %H:%M:%S'

    def __init__(self, with_videos):
        self.support = set([
            'image',
        ])
        if with_videos:
            self.support.add('video')

        self.dates = (
            ('CreateDate', self._exif_dt),
            ('DateTimeOriginal', self._exif_dt),
            ('ModifyDate', self._exif_dt),
            ('FileModifyDate', self._exif_dt + '%z'),
        )

    def __call__(self, exif, suffix):
        #
        # Make sure the file type is supported
        #
        (mime, _) = exif['MIMEType'].split('/', maxsplit=1)
        if mime.casefold() not in self.support:
            raise TypeError(f'Unsupported file type "{mime}"')

        #
        # Use the time to build a filename
        #
        ctime = (self
                 .mktime(exif)
                 .strftime('%Y %m-%b %d-%H%M%S')
                 .upper()
                 .split())
        path = Path(*ctime)

        return path.with_suffix(suffix)

    #
    # Extract the time at which the picture was taken
    #
    def mktime(self, exif):
        for (k, s) in self.dates:
            creation = exif.get(k)
            try:
                return datetime.strptime(creation, s)
            except (TypeError, ValueError):
                logging.debug(f'Invalid {k}: "{creation}"')

        raise ValueError('Cannot establish creation time')

#
# Use the time to create a destination file name
#
class PathName:
    @staticmethod
    def zcount(upper):
        if upper < 1:
            raise ArithmeticError('Max count must be greater than zero')
        digits = math.floor(math.log10(upper - 1)) + 1

        for i in it.count():
            if i >= upper:
                break
            yield f'{i:0{digits}d}'

    def __init__(self, destination, lock, maxtries):
        self.destination = destination
        self.lock = lock
        self.maxtries = maxtries

    def __call__(self, path):
        basename = path.with_suffix('')

        self.lock.acquire()
        try:
            for i in self.zcount(self.maxtries):
                fname = f'{basename}-{i}{path.suffix}'
                target = self.destination.joinpath(fname)
                if not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.touch()

                    return target
        finally:
            self.lock.release()

        raise FileExistsError('Cannot create unique filename')

def func(queue, lock, args):
    exif2path = ExifPath(args.with_videos)
    path2fname = PathName(args.destination, lock, args.maxtries)
    mode = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH

    while True:
        exif = queue.get()
        source = Path(exif['SourceFile'])

        try:
            path = exif2path(exif, source.suffix.lower())
            target = path2fname(path)
            (src, dst) = map(str, (source, target))
            shutil.copy2(src, dst)
            os.chmod(dst, mode)
            logging.info('{} -> {}'.format(source.name, target))
        except (TypeError, ValueError, FileExistsError) as err:
            logging.error('{} {}'.format(source, err))
        finally:
            queue.task_done()

if __name__ == '__main__':
    arguments = ArgumentParser()
    arguments.add_argument('--destination', type=Path)
    arguments.add_argument('--maxtries', type=int, default=100)
    arguments.add_argument('--with-videos', action='store_true')
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
