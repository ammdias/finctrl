"""
SQLitesTore: base storage classe to ease the use of sqlite3 databases
"""

__version__ = '0.1'
__date__ = '2021-03-21'
__author__ = 'António Manuel Dias <ammdias@gmail.com>'
__license__ = """
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os.path
import sqlite3

#-----------------------------------------------------------------------------
class SQLiteStore:
    """Base storage classe to ease the use of sqlite3 databases
    """

    def __init__(self, storepath, create=False, **metadata):
        """Connect to database creating it if required and necessary.

        storepath: path to sqlite3 storage file
        create: set to True to create database on non-existing path
        metadata: key-value pairs of meta data to set in database
        """
        self._db = None
        self._dbpath = storepath.strip()
        if not self._dbpath:
            raise ValueError("Path to the storage not provided.")
        if not create and not os.path.exists(self._dbpath):
            raise ValueError(f"Could not open storage file at '{self._dbpath}'")

        try:
            self._db = sqlite3.connect(self._dbpath)
            # SQLiteStore connection shortcuts
            self._exec = self._db.execute
            self._exmany = self._db.executemany
            self._script = self._db.executescript
            self._commit = self._db.commit
            self._rollback = self._db.rollback
        except:
            raise ValueError(f"Could not open storage file at '{storepath}'")

        with self._db:
            if create:
                self._script(_SCRIPT_CREATE)
            # set metadata if present
            if metadata:
                for key, value in metadata.items():
                    self.set_metadata(key, value)


    def __del__(self):
        """Ensure database is in good state before destroying object.
        """
        if self._db:
            self._db.commit()
            self._db.close()


    def backup(self, backuppath, progress=None):
        """Backup current database to another file.
        """
        try:
            with sqlite3.connect(backuppath) as bkp:
                self._db.backup(bkp, progress=progress)
        except Exception as e:
            raise ValueError(f"Could not create backup file at '{backuppath}'")


    def set_metadata(self, key, value):
        """Insert/update metadata value with given key.
           If key does not exist in metadata table, insert it.
        """
        if self._exists("metadata", "key", key):
            self._do("update metadata set value=? where key=?", (value, key))
        else:
            self._do("insert into metadata values (?,?)", (key, value))


    def metadata(self, key):
        """Return metadata value by key if it exists or None.
        """
        if not self._exists("metadata", "key", key):
            return None
        return self._qry1("select value from metadata where key=?", (key,))[0]


    def remove_metadata(self, key):
        """Remove metadata tuple with given key, if it exists.
        """
        self._do("delete from metadata where key=?", (key,))


    # SQLiteStore access functions

    def _do(self, *qry):
        """Execute the query and commit changes.
        """
        with self._db:
            return self._exec(*qry)

    def _domany(self, *qry):
        """Execute the query for the sequence and commit changes.
        """
        with self._db:
            self._exmany(*qry)

    def _qry(self, *qry):
        """Execute the query and return a list of results.
        """
        return self._exec(*qry).fetchall()

    def _qry1(self, *qry):
        """Execute the query and return a list with a single result.
        """
        return self._exec(*qry).fetchone()

    def _exists(self, table, field, value):
        """Find if value is present in a table field.
           'table' and 'field' values MUST by checked by the calling code.
        """
        return self._qry1(f"select count(*) from {table} where {field}=?",
                         (value,))[0] > 0


# -----------------------------------------------------------------------------
# SQL script to create metada table

_SCRIPT_CREATE = """
create table metadata (
     key         text not null,
     value       text not null,
     primary key (key)
);
"""
