FINANCE CONTROL
===============

(C) 2021 António Manuel Dias

Changes List:
    * 0.12  `add tag` and `delete tag` now also accept tag lists as arguments
            and may be called in the form `add tags` and `delete tags`;
            `list transactions of` now also accepts an amount range as argument.
            Currency values now include currency symbol. Input values may also
              contain currency symbols (not required);
            Lines starting with empty space followed by comment are now ignored;
            Empty lines are no longer printed when 'echo' is on;
            An empty line on the end of a multiline command now terminates the
              command input;
            Corrected bug in delete transaction (only delete from history if
              present);
            Updated manual.

    * 0.11: Added option to list transactions of a certain amount.

    * 0.10: Added uninstall option.
            Updated install script and manual.

    * 0.9: Added greeting to application start;
           Added new command: `show last`;
           Added reverse order option for `list transactions`,
             `list parcels`, `find transactions` and `find parcels` commands
           Comments are now accepted (and ignored) in the command line;
           Corrected uncatched exception in FinCtrlCmd.do_source();
           Corrected bug in FinCtrlCmd._change_currency();
           Updated manual;
           Install script now catches all exceptions ocurred;
           Normalized copyright notices in files.

    * 0.8.2: Corrected inline documentation.

    * 0.8.1: Corrected bug in `list transactions`.

    * 0.8: Source command now ignores lines started with semicolon;
           List transactions now supports listing on multiple accounts.

    * 0.7: Added option `top` to `list transactions`, `list parcels tagged`,
           `find transactions` and `find parcels` commands.

    * 0.6: New commands: find transactions and find parcels.

    * 0.5: Blank input on multiple page listings will advance page and quit
           at last page.

    * 0.4: List accounts, transactions and parcels now show total amounts;
           Added extra lines in table printings for better presentation;
           Navigation in multi-page listings may be done by page number.

    * 0.3.1: Corrected bug in `list transactions`.

    * 0.3: Corrected bug in `finutil.d2i()` which prevented parsing of decimal
           numbers without leading integer part.

    * 0.2: Added `edit` option to `source` command (`finctrlcmd.FinCtrlCmd`);
           Corrected bug in `set csvsep` command (`finctrlcmd.FinCtrlCmd`).

    * 0.1: Initial version.
