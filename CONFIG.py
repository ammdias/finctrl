'''Configuration file for the Finance Control installation script.
'''

DOC = 'Installation script for Finance Control.'''
COPYRIGHT_YEAR = '2021'
VERSION = '0.12'
DATE = '2024-07-31'
AUTHOR = 'António Manuel Dias <ammdias@gmail.com>'
LICENSE = '''
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
'''


# List of file to be copied to installation the directory
FILES = ('finctrlcmd.py', 'finctrl.py', 'finstore.py', 'finutil.py',
         'sqlitestore.py', 'UNINSTALL.py',
         'LICENSE.md', 'LICENSE.html', 'MANUAL.md', 'MANUAL.html',
         'README.md', 'CHANGES.md', 'food.csv.png', '__version__')

# List of directories to be copied to the installation directory
TREES = ()

# Name of the icon file
ICO_FILE = None

# Name of the desktop entry file (for GUI menus)
DESKTOP_FILE = None

# Files to make executable
EXECS = ('finctrl.py',)

# Name of the application (will be the name of the installation directory)
APP_NAME = 'FinCtrl'

# Symbolic links to make: dictionary of 'link name': 'executable name' pairs
LINKS = {'finctrl': 'finctrl.py'}

# List of configuration files
CONFIG_FILES = ()
