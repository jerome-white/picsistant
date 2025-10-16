import sqlite3
import operator as op
from pathlib import Path
from argparse import ArgumentParser
from contextlib import closing

from pictilities import Logger

def deleted(db):
    with closing(sqlite3.connect(db)) as con:
        with closing(con.cursor()) as cur:
            res = cur.execute('''
            SELECT ZDIRECTORY || "/" || ZFILENAME
            FROM ZASSET
            WHERE ZTRASHEDSTATE IS TRUE
            ''')

            yield from map(op.itemgetter(0), res)

def locate(results):
    for r in results:
        path = Path(r)
        yield from path.parent.rglob(f'{path.stem}.*')

def resolve(path):
    db = path
    if db.is_dir():
        db = (db
              .joinpath('database', 'Photos')
              .with_suffix('.sqlite'))
    if not db.exists():
        err = f'Cannot infer database location from {path}'
        raise FileNotFoundError(err)

    return db

if __name__ == '__main__':
    arguments = ArgumentParser()
    arguments.add_argument('--photos-db', type=Path)
    arguments.add_argument('--dry-run', action='store_true')
    args = arguments.parse_args()

    for path in locate(deleted(resolve(args.photos_db))):
        Logger.info(path)
        if not args.dry_run:
            path.unlink(missing_ok=True)
