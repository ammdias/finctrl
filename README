FINANCE CONTROL README
======================
version 0.1

Copyright (C) 2021 António Manuel Dias

contact: ammdias@gmail.com

website: https://ammdias.duckdns.org/downloads

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see http://www.gnu.org/licenses/.


Changes history:

* 0.1: Initial version


ABOUT THE PROGRAM
=================

This is a very basic program to control personal finances.  It depends on
Python 3 and was thought to be used only from the command line.  It
supports multiple accounts with possibly different coin units and transactions
composed of multiple parcels, each with its differente tags.  Check the MANUAL
for a more complete overview of the program.

The following instructions are for Linux systems.  If you intend to use the
program on another system, please refer to the included MANUAL.


INSTALLATION AND BASIC USAGE
============================

The following instructions describe the installation process for basic usage
in a Linux environment.  For more advanced instructions, including MS Windows
usage, please refer to the user manual in the file "MANUAL" or "MANUAL.pdf".

1. Open a terminal and change to the directory where you uncompressed the
   program.  Execute the local installation script:

       $ bash local_install.sh

   This will copy the program to the current user's "~/.local/lib" hidden
   directory and create a symbolic link to the program in "~/.local/bin",
   which should be in the user's PATH.

2. To check that the program is working, open *another* terminal and type:

       $ finctrl

   This should open the program and present its default prompt.  If not, check
   if "~/.local/bin" is in the PATH with the following command:

       $ echo $PATH

   Also, check that the program was copied to the locations mentioned above
   and that the symbolic link was created.

3. If the program is working, check that it responds to commands:

       FinCtrl > help
       (the program should present a list of all the available commands)

       FinCtrl > bye
       (the program should close; you may also use the end-of-file
        command -- CTRL-D in Linux -- to close the program)

4. Read the MANUAL.  You can open it in a web borwser from the program with the
   command:

      FinCtrl > manual
