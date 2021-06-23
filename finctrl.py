#!/usr/bin/env python3

"""
Finance Control

An application to control personal finances.
"""

__version__ = '0.3.1'
__date__ = '2021-06-23'
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

Changes:
    0.3.1: Corrected bug in 'list transactions'.
    0.3: Corrected bug in finutil.d2i() which prevented parsing of decimal
         numbers without leading integer part.
    0.2: Added 'edit' option to 'source' command (finctrlcmd.FinCtrlCmd)
         Corrected bug in 'set csvsep' command (finctrlcmd.FinCtrlCmd)
    0.1: Initial version.
"""


import argparse

from finctrlcmd import FinCtrlCmd


#------------------------------------------------------------------------------
# parse command line arguments

parser = argparse.ArgumentParser()
parser.add_argument("file", type=str, nargs='?', help="file to open.")
parser.add_argument("-s", "--source", type=str, help="file to be executed.")
args = parser.parse_args()


#------------------------------------------------------------------------------
# Start application

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

