#!/usr/bin/env python3

"""
Finance Control

An application to control personal finances.
"""

__version__ = '0.12'
__date__ = '2024-07-31'
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


import sys
import os.path
import argparse

from finctrlcmd import FinCtrlCmd


#------------------------------------------------------------------------------
# parse command line arguments

parser = argparse.ArgumentParser()
parser.add_argument("file", type=str, nargs='?', help="file to open.")
parser.add_argument("-s", "--source", type=str, help="file to be executed.")
parser.add_argument("--uninstall", action="store_true",
                    help="uninstall application.")
args = parser.parse_args()


#------------------------------------------------------------------------------
# Start application

# Uninstall the application
if args.uninstall:
    from UNINSTALL import uninstall
    uninstall()

# Print application greeting
try:
    appver = open(os.path.join(sys.path[0], '__version__')).read().strip()
except:
    appver = __version__
print('Finance Control')
print('Version:', appver)
print('Copyright (C) 2021', __author__)
print(__license__)

fincmd = FinCtrlCmd()

if args.source:
    fincmd.preloop()
    fincmd.do_source(args.source)
else:
    if args.file:
        fincmd.do_open(args.file)
    try:
        fincmd.cmdloop()
    except KeyboardInterrupt:
        print("Program interrupted by user.\n"
              "Please use 'bye' command next time.")

