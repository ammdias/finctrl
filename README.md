FINANCE CONTROL README
======================
version 0.10

Copyright (C) 2021 António Manuel Dias

contact: ammdias@gmail.com

website: [AMMDIAS GitHub](https://github.com/ammdias/finctrl)

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


ABOUT THE PROGRAM
=================

This is a very basic program to control personal finances.  It depends on
**Python 3** and was thought to be **used only from the command line**.  It
supports multiple accounts with possibly different currencies and transactions
composed of multiple parcels, each with its different tags.  Check the
[MANUAL](MANUAL.html) for a more complete overview of the program.

This is what the program IS NOT and CANNOT DO:

* It will not contact your home banking system;
* It will not scan your bills and insert them automatically;
* It will not produce beautiful (or even ugly) graphics;
* It will not analyse your savings and make predictions on where you will be in
  ten years;
* It will not automatically add interest rates to your savings accounts or
  loans.

This is what it CAN DO:

* Record your earnings and expenses exactly as you enter them;
* List your earnings and expenses filtered by date, account and/or item tags;
* Export your listings to CSV files that can be further processed in other
  tools like spreadsheet applications.

The following instructions are for Linux systems.  If you intend to use the
program on another system, please refer to the included MANUAL.


INSTALLATION AND BASIC USAGE
============================

The following instructions describe the installation process for basic usage
in a Linux environment.  For more advanced instructions, including MS Windows
usage, please refer to the user manual in the file "MANUAL.md" or "MANUAL.html".

1. Open a terminal in the directory where the program was uncompressed and run
   the installation script with Python 3:

         $ python3 INSTALL.py

     You will be prompted for the installation directory --- i.e. the directory
     under which the folder containing all the application files will be placed
     --- and for the start link directory --- i.e. the directory where the
     symbolic link for the program will be created.

     The default directories will install the program for the current user only
     and are suited for single-user systems.  If you want to keep these
     settings, just press ENTER when prompted.  The program will be installed in
     the directory `$HOME/.local/lib/FinCtrl` and the symbolic link
     `$HOME/.local/bin/finctrl` will be created.  On most Linux systems the
     `$HOME/.local/bin` directory will be inserted in the execution PATH, if it
     exists. If it doesn't, you will have to add it manually.

     If you want to install the program for all the users of the system, you
     should change the directories accordingly, e.g. `/usr/local/lib` for the
     installation directory and `/usr/local/bin` for the start link.  Of
     course, you will need to run the installation script with administration
     privileges:

         $ sudo python3 INSTALL.py

     If a previous installation exists on the selected directory, you will be
     asked if you want to overwrite it.  Answer "`yes`" (or just "`y`") if that
     is the case or "`no`"/"`n`" if not.

2. Test that the installation was successful with the command:

       $ finctrl

   (this should open the program and present its default prompt)

   Now, enter the following commands:

       FinCtrl > help

   (the program should present a list of all the available commands)

       FinCtrl > bye

   (the program should close; you may also use the end-of-file
   command -- CTRL-D in Linux -- to close the program)

3. Read the MANUAL.  You can open it in a web browser from the program with the
   command:

       FinCtrl > show manual
 
