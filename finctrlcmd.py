"""
Finance Control command line interface
"""

__version__ = '0.8'
__date__ = '2022-08-24'
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
__changes__ = """
    0.8: Source command now ignores lines started with semicolon;
         List transactions now supports listing on  multiple accounts;
         Set echo command now ignores argument case.
    0.7: Added 'top' keyword to 'list transactions', 'list parcels'
         'find transactions' and 'find parcels' commands
    0.6: Add transfer completely fails if one of the transactions fails;
         Added 'find transactions' and 'find parcels' commands.
    0.5: Blank input on multiple page listings advances one page and quits
         on last page
    0.4: List accounts, transactions and parcels now show amount totals;
         Added extra lines in table printings for better presentation;
         Navigation in multi-page listing may be done by page number.
    0.3.1: Corrected bug in 'list transactions'.
    0.3: Removed unused symbol in FinCtrlCmd.
    0.2: Added 'edit' option to 'source' command.
         Corrected bug in 'set csvsep' command.
    0.1: Initial version.
"""

import cmd
import sys
import shlex
import os             # for os.path and os.environ
import subprocess
import webbrowser

from finutil import *
from finstore import FinStore


#-----------------------------------------------------------------------------
# Default general settings

DEFAULTS = {
        'prompt': 'FinCtrl > ',
        'csvsep': ';',
        'editor': '',
        'currency': 'default',
        'withdrawal': 'Withdrawal',
        'deposit': 'Deposit',
        'transfer': 'Transfer'
}


#-----------------------------------------------------------------------------

class FinCtrlCmd(cmd.Cmd):
    """
    Finance Control command line interface class.
    """
    prompt = DEFAULTS['prompt']
    _store = None
    echo = False

    #-------------------------------------------------------------------------
    # Setup and configuration methods
    def preloop(self):
        """Reset multiline command state before starting the command loop.
        """
        self._saved_prompt = None
        self._multilncmd = []


    def precmd(self, line):
        """Provide support for multiline commands.
        """
        # check for multiline commands (last token is a single backslash)
        line = line.split()
        if line and line[-1] == '\\':
            del line[-1]
            self._multilncmd += line
            if not self._saved_prompt:
                self._saved_prompt = self.prompt
                self.prompt = ' ' * (len(self.prompt)-2) + ': '
            line = ''
        else:
            if line and line[-1] == '\\\\\\':
                line = ''
            else:
                line = ' '.join(self._multilncmd + line)
            # restore prompt after multiline command
            if self._saved_prompt:
                self.prompt = self._saved_prompt
                self._saved_prompt = None
                self._multilncmd = []

        if self.echo:
            print(line)
        return line


    def default(self, line):
        """Print error message on unknown command.
        """
        cmd = line.split()[0]
        error(f"(Syntax) '{cmd}' is not a recognized command.")


    def emptyline(self):
        """Do nothing when user inserts an empty line.
        """


    #-------------------------------------------------------------------------
    # Command methods

    def do_open(self, arg):
        """Open a Finance Control database file:
        > open FILE
        """
        arg = os.path.expanduser(arg)
        try:
            if os.path.exists(arg):
                self._store = FinStore(arg)
            else:
                self._store = FinStore(arg, True, **DEFAULTS)
                fname = os.path.split(arg)[1]
                self._store.set_metadata('prompt', fname + ' > ')
            self.prompt = self._store.metadata('prompt') 
            self.csvsep = self._store.metadata('csvsep')
            if not self.prompt or not self.csvsep:
                self._store = None
                self.prompt = DEFAULTS['prompt']
                error("File is not a Finance Control file or is corrupted.")
        except Exception as e:
            self._store = None
            error(f"unable to open file. Reason:\n    {e}")


    def do_close(self, arg):
        """Close the current database file.
        > close
        """
        self._store = None
        self.prompt = DEFAULTS['prompt']


    def do_backup(self, arg):
        """Backup current database to a different file:
        > backup FILE
        """
        if not self._store:
            error("'backup' command needs an open file.")
            return

        if not arg:
            error("'backup' syntax:\n"
                  "    > backup FILE")
            return

        arg = os.path.expanduser(arg)
        if os.path.exists(arg):
            if not yesno(f"'{arg}' already exists. Overwrite it?"):
                return
            try:
                os.remove(arg)
            except:
                error("Could not overwrite the file. Backup failed.")
                return
        try:
            self._store.backup(arg)
        except Exception as e:
            error(f"backup failed. Reason:\n    {e}")


    def do_trim(self, arg):
        """Remove all records previous to a specific date:
        > trim acc[ount] ACCOUNT_NAME|ACCOUNT_ID upto DATE
        > trim storage upto DATE
        """
        if self._store:
            self._dispatch('trim', arg)
        else:
            error("'trim' command needs an open file.")


    def do_source(self, arg):
        """Execute commands from a file.
        > source [edit] FILE
        """
        args = shlex.split(arg)
        if 'edit' in args:
            edit = True
            args.remove('edit')
        else:
            edit = False

        if len(args) != 1:
            error("'source' command syntax:\n"
                  "    > source [edit] FILE")
            return

        fname = os.path.expanduser(args[0])
        if edit:
            self._editfile(fname)

        echo, self.echo = self.echo, True
        try:
            for line in open(fname, 'r'):
                if line.startswith(';'):  # ignore comment lines
                    continue
                line = self.precmd(line)
                if line:
                    self.onecmd(line)
        except Exception as e:
            error(f"Could not read the file. Reason:\n    {e}")
        finally:
            self.echo = echo


    def do_set(self, arg):
        """Set metadata on the current database file:
        > set csvsep CHARACTER
        > set curr[ency] NAME
        > set deposit descr[iption] TEXT
        > set echo ON|OFF
        > set editor TEXT
        > set prompt TEXT
        > set transfer descr[iption] TEXT
        > set withdrawal descr[iption] TEXT
        """
        if self._store or 'echo' in arg:
            self._dispatch('set', arg)
        else:
            error("'set' command needs an open file.")


    def do_add(self, arg):
        """Insert data or a record on the current database file:
        > add acc[ount] TEXT [descr[iption] TEXT] [curr[ency] NAME]
        > add curr[ency] TEXT [short TEXT] [symbol TEXT] [position LEFT|RIGHT] \\
        :                [decplaces NUMBER] [decsep CHARACTER]
        > add deposit of AMOUNT on ACCOUNT_NAME|ACCOUNT_ID \\
        :             [descr[iption] TEXT] [date DATE] [tags LIST]
        > add exp[ense] on ACCOUNT_NAME|ACCOUNT_ID \\
        :               [descr[iption] TEXT] [date DATE] \\
        :               of AMOUNT | parcel "TEXT AMOUNT [tags LIST]" ...
        > add parcel TEXT of AMOUNT to TRANSACTION_ID [tags LIST]
        > add tag TEXT to PARCEL_ID
        > add tr[ansaction] on ACCOUNT_NAME|ACCOUNT_ID \\
        :                   [neg] [descr[iption] TEXT] [date DATE] \\
        :                   of AMOUNT | parcel "TEXT AMOUNT [tags LIST]" ...
        > add transfer of AMOUNT [descr[iption] TEXT] [date DATE] [tags LIST]
        :              from ACCOUNT_NAME|ACCOUNT_ID to ACCOUNT_NAME|ACCOUNT_ID
        > add withdrawal of AMOUNT on ACCOUNT_NAME|ACCOUNT_ID \\
        :                [descr[iption] TEXT] [date DATE] [tags LIST]
        """
        if self._store:
            self._dispatch('add', arg)
        else:
            error("'add' command needs an open file.")


    def do_delete(self, arg):
        """Remove data or a record from the current database file:
        > de[lete] acc[ount] ACCOUNT_NAME|ACCOUNT_ID
        > de[lete] parcel PARCEL_ID
        > de[lete] tag TEXT from PARCEL_ID
        > de[lete] tag TEXT
        > de[lete] tr[ansaction] TRANSACTION_ID
        """
        if self._store:
            self._dispatch('delete', arg)
        else:
            error("'delete' command needs an open file.")

    # shortcut
    do_del = do_delete


    def do_change(self, arg):
        """Change a record in the current database file:
        > ch[ange] acc[ount] ACCOUNT_NAME|ACCOUNT_ID descr[iption] to TEXT
        > ch[ange] acc[ount] ACCOUNT_NAME|ACCOUNT_ID name to TEXT
        > ch[ange] curr[ency] NAME [short TEXT] \\
        :                     [symbol TEXT] [position LEFT|RIGHT] \\
        :                     [decplaces NUMBER] [decsep CHARACTER]
        > ch[ange] parcel PARCEL_ID amount to AMOUNT
        > ch[ange] parcel PARCEL_ID descr[iption] to TEXT
        > ch[ange] tag TAG to TEXT
        > ch[ange] tr[ansaction] TRANSACTION_ID acc[ount] \\
        :                      to ACCOUNT_NAME|ACCOUNT_ID
        > ch[ange] tr[ansaction] TRANSACTION_ID date to DATE
        > ch[ange] tr[ansaction] TRANSACTION_ID descr[iption] to TEXT
        """
        if self._store:
            self._dispatch('change', arg)
        else:
            error("'change' command needs an open file.")

    # shortcut
    do_ch = do_change


    def do_show(self, arg):
        """Show a specific record's data:
        > sh[ow] acc[ount] ACCOUNT_NAME|ACCOUNT_ID
        > sh[ow] curr[ency] NAME
        > sh[ow] settings|manual [inline]|copyright|license [inline]
        > sh[ow] tr[ansaction] TRANSACTION_ID
        """
        if self._store or \
                'manual' in arg or 'copyright' in arg or 'license' in arg:
            self._dispatch('show', arg)
        else:
            error("'show' command needs an open file.")

    # shortcut
    do_sh = do_show


    def do_list(self, arg):
        """List database records:
        > list|ls acc[ounts] [ACCOUNT_NAME] [tofile FILE]
        > list|ls curr[encies] [NAME] [tofile FILE]
        > list|ls parcels tagged LIST [from DATE] [to DATE] \\
                                      [top NUMBER] [tofile FILE]
        > list|ls tags [tofile FILE]
        > list|ls tr[ansactions] [on ACCOUNT_NAME|ACCOUNT_ID] \\
        :                        [from DATE] [to DATE] \\
                                 [top NUMBER] [tofile FILE]
        """
        if self._store:
            self._dispatch('list', arg)
        else:
            error("'list' command needs an open file.")

    # shortcut
    do_ls = do_list


    def do_find(self, arg):
        """Find text in descriptions.
        > find tr[ansactions] like TEXT [from DATE] [to DATE] \\
                                        [top NUMBER] [tofile FILE]
        > find parcels like TEXT [from DATE] [to DATE] \\
                                 [top NUMBER] [tofile FILE]
        """
        if self._store:
            self._dispatch('find', arg)
        else:
            error("'find' command needs an open file.")


    #---- Quit commands

    def do_bye(self, arg):
        """Quit Finance Control.
        """
        print('Bye.')
        return True

    do_EOF = do_bye


    #---- Complex command dispatcher

    def _dispatch(self, prefix, arg):
        """Command dispatcher.
        """
        try:
            args = shlex.split(arg)
            if args:
                cmd = f'_{prefix}_{args.pop(0)}'
                getattr(self, cmd)(args)
            else:
                self.do_help(prefix)
        except AttributeError:
            error(f"'{prefix}' command syntax:")
            self.do_help(prefix)
        except Exception as e:
            error(e)


    #-------------------------------------------------------------------------
    # Work methods

    def _trim_storage(self, args):
        """Trim database file up to a date.
        """
        pos, kw, mkw = parse_args(args, 'upto')
        if pos or 'upto' not in kw or mkw:
            raise Exception("'trim' command syntax:\n"
                            "    > trim storage upto DATE")

        try:
            date = parse_date(kw['upto'])
            self._store.trim(date)
        except Exception as e:
            error(f"unable to trim file. Reason:\n    {e}")


    def _trim_account(self, args):
        """Trim account up to a date.
        """
        pos, kw, mkw = parse_args(args, 'upto')
        if len(pos) != 1 or 'upto' not in kw or mkw:
            raise Exception("'trim' command syntax:\n"
                            "    > trim account ACCOUNT_NAME|ACCOUNT_ID upto DATE")

        try:
            date = parse_date(kw['upto'])
            acckey = self._store.account_key(pos[0])
            if acckey:
                self._store.trim(date, acckey)
            else:
                error('Account not found.')
        except Exception as e:
            error(f"unable to trim account. Reason:\n    {e}")

    # shortcut
    _trim_acc = _trim_account


    def _set_echo(self, args):
        """Set command echo print on or off.
        """
        if len(args) != 1 or args[0].lower() not in ('on', 'off'):
            raise Exception("'set echo' command takes a single argument:\n"
                            "    > set echo ON|OFF")

        self.echo = (args[0].lower() == 'on')


    def _set_prompt(self, args):
        """Set prompt.
        """
        if len(args) != 1:
            raise Exception("'set prompt' command takes a single argument:\n"
                            "    > set prompt TEXT")

        try:
            self._store.set_metadata('prompt', args[0])
            self.prompt = self._store.metadata('prompt') 
        except Exception as e:
            error(f"unable to set prompt. Reason:\n    {e}")


    def _set_csvsep(self, args):
        """Set field separator for CSV files.
        """
        if len(args) != 1 or len(args[0]) != 1:
            raise Exception("'set csvsep' syntax:\n"
                            "    > set csvsep CHARACTER")

        try:
            self._store.set_metadata('csvsep', args[0])
            self.csvsep = self._store.metadata('csvsep') 
        except Exception as e:
            error(f"unable to set csvsep. Reason:\n    {e}")


    def _set_currency(self, args):
        """Set currency.
        """
        if len(args) != 1:
            raise Exception("'set currency syntax:\n"
                            "    > set curr[ency] NAME")

        try:
            curr = self._store.currency(args[0])
            self._store.set_metadata('currency', curr.name)
        except Exception as e:
            error(f"unable to set currency. Reason:\n    {e}")

    # shorcut
    _set_curr = _set_currency


    def _set_deposit(self, args):
        """Set deposit default text.
        """
        self._setdescr('deposit', args)


    def _set_editor(self, args):
        """Set editor command.
        """
        if len(args) != 1:
            raise Exception("'set editor syntax:\n"
                            "    > set editor TEXT")

        try:
            self._store.set_metadata('editor', args[0])
        except Exception as e:
            error(f"unable to set editor. Reason:\n    {e}")


    def _set_withdrawal(self, args):
        """Set withdrawal default text.
        """
        self._setdescr('withdrawal', args)


    def _set_transfer(self, args):
        """Set transfer default text.
        """
        self._setdescr('transfer', args)


    def _add_currency(self, args):
        """Add currency.
        """
        pos, kw, mkw = parse_args(args, 'short', 'symbol', 'position',
                                        'decplaces', 'decsep')
        if len(pos) != 1 or mkw:
            raise Exception("'add currency' syntax:\n"
                "    > add curr[ency] TEXT [short TEXT] \\\n"
                "    :                [symbol TEXT] [position LEFT|RIGHT] \\\n"
                "    :                [decplaces NUMBER] [decsep TEXT]")

        try:
            curr = self._store.currency('default')
            curr.name = pos[0].strip()
            curr.short_name = kw.get('short', curr.short_name)
            curr.symbol = kw.get('symbol', curr.symbol)
            spos = kw.get('position', curr.symbol_pos).strip().lower()
            if spos not in ('left', 'right'):
                raise ValueError("currency symbol position must be 'left' or 'right'")
            curr.symbol_pos = spos
            curr.dec_places = int(kw.get('decplaces', curr.dec_places))
            curr.dec_sep = kw.get('decsep', curr.dec_sep)
            self._store.add_currency(curr)
        except Exception as e:
            error(f"unable to add currency. Reason:\n    {e}")

    _add_curr = _add_currency


    def _add_account(self, args):
        """Add account.
        """
        pos, kw, mkw = parse_args(args, 'descr', 'description',
                                        'curr', 'currency')
        if len(pos) != 1 or mkw:
            raise Exception("'add account' syntax:\n"
            "    > add acc[ount] TEXT [descr[iption] TEXT] [curr[ency] NAME]")
        try:
            curr = kw.get('curr', kw.get('currency',
                                         self._store.metadata('currency')))
            curr = self._store.currency(curr)
            a = FinStore.Account()
            a.name = pos[0]
            a.descr = kw.get('descr', kw.get('description', ''))
            a.currency = curr.name
            self._store.add_account(a)
        except Exception as e:
            error(f"unable to add account. Reason:\n    {e}")

    # shortcut
    _add_acc = _add_account


    def _add_deposit(self, args):
        """Add deposit.
        """
        pos, kw, mkw = parse_args(args, 'on', 'of', 'descr', 'description',
                                        'date', 'tags')
        if pos or mkw or 'on' not in kw or 'of' not in kw:
            raise Exception("'add deposit' syntax:\n"
                  "    > add deposit of AMOUNT on ACCOUNT_NAME|ACCOUNT_ID \\\n"
                  "    :             [descr[iption] TEXT] [date DATE] [tags LIST]")

        t = self._addtr(kw, descr=self._store.metadata('deposit'), mul=1)
        print(f"Transaction id: {t}")


    def _add_withdrawal(self, args):
        """Add withdrawal.
        """
        pos, kw, mkw = parse_args(args, 'on', 'of', 'descr', 'description',
                                        'date', 'tags')
        if pos or mkw or 'on' not in kw or 'of' not in kw:
            raise Exception("'add withdrawal' syntax:\n"
                  "    > add withdrawal of AMOUNT on ACCOUNT_NAME|ACCOUNT_ID \\\n"
                  "    :                [descr[iption] TEXT] [date DATE] [tags LIST]")

        t = self._addtr(kw, descr=self._store.metadata('withdrawal'), mul=-1)
        print(f"Transaction id: {t}")


    def _add_transfer(self, args):
        """Add transfer of amount between two accounts.
        """
        pos, kw, mkw = parse_args(args, 'from', 'to', 'of',
                                        'descr', 'description', 'date', 'tags')
        if pos or mkw or 'from' not in kw or 'to' not in kw or 'of' not in kw:
            raise Exception("'add transfer' syntax:\n"
                  "    > add transfer of AMOUNT \\\n"
                  "    :   [descr[iption] TEXT] [date DATE] [tags LIST] \\\n"
                  "    :   from ACCOUNT_NAME|ACCOUNT_ID to ACCOUNT_NAME|ACCOUNT_ID")

        try:
            t1, t2, descr = None, None, self._store.metadata('transfer')
            kw['on'] = kw['from']
            t1 = self._addtr(kw, descr=descr, mul=-1)
            kw['on'] = kw['to']
            t2 = self._addtr(kw, descr=descr)
        except Exception as e:
            error(f"unable to add transfer. Reason:\n    {e}")
            try:
                if t1 is not None:
                    self._store.del_transaction(t1)
                if t2 is not None:
                    self._store.del_transaction(t2)
            except Exception as e:
                error(f"unable to delete transaction. Reason:\n    {e}")
        else:
            print(f"Transaction ids: {t1}, {t2}")


    def _add_transaction(self, args):
        """Add transaction.
        """
        parcels, mul = [], 1
        pos, kw, mkw = parse_args(args, 'on', 'of', 'descr', 'description',
                                        'date', 'tags', 'parcel')
        if 'neg' in pos:
            mul = -1
            pos.remove('neg')

        if pos or 'on' not in kw or \
           ('of' not in kw and 'parcel' not in kw and not mkw) \
           or (len(mkw) == 1 and 'parcel' not in mkw) or len(mkw) > 1:
            raise Exception("'add transaction' syntax:\n"
                  "    > add tr[ansaction] on ACCOUNT_NAME|ACCOUNT_ID \\\n"
                  "    :     [neg] [descr[iption] TEXT] [date DATE] \\\n"
                  '    :     of AMOUNT | parcel "TEXT AMOUNT [tags LIST]" ... ')

        if 'of' not in kw:
            parcels = [kw['parcel']] if 'parcel' in kw else mkw['parcel']

        t = self._addtr(kw, parcels=parcels, mul=mul)
        print(f"Transaction id: {t}")

    # shortcut
    _add_tr = _add_transaction


    def _add_expense(self, args):
        """Add expense (negative amount transaction).
        """
        args.insert(0, 'neg')
        self._add_transaction(args)

    _add_exp = _add_expense


    def _add_parcel(self, args):
        """Add parcel to an existing transaction.
        """
        pos, kw, mkw = parse_args(args, 'to', 'of', 'tags')
        if len(pos) != 1 or 'to' not in kw or 'of' not in kw or mkw:
            raise Exception("'add parcel' syntax:\n"
                  "    > add parcel TEXT of AMOUNT to TRANSACTION_ID [tags LIST]")
        try:
            p = FinStore.Parcel()
            p.trans= kw['to']
            p.descr = pos[0]
            curr = self._store.transaction_currency(p.trans)
            p.amount = d2i(kw['of'], curr)
            if 'tags' in kw:
                p.tags = parse_tags(kw['tags'])
            self._store.add_parcel(p)
        except Exception as e:
            error(f"unable to add parcel. Reason:\n    {e}")


    def _add_tag(self, args):
        """Add tag to an existing parcel.
        """
        pos, kw, mkw = parse_args(args, 'to')
        if len(pos) != 1 or 'to' not in kw or mkw:
            raise Exception("'add parcel' syntax:\n"
                            "    > add tag TEXT to PARCEL_ID")
        try:
            self._store.add_parcel_tag(kw['to'], pos[0])
        except Exception as e:
            error(f"unable to add tag. Reason:\n    {e}")


    def _delete_account(self, args):
        """Delete account.
        """
        if len(args) != 1:
            raise Exception("'delete account' syntax:\n"
                            "    > del[ete] acc[ount] ACCOUNT_NAME|ACCOUNT_ID")
        try:
            acckey = self._store.account_key(args[0])
            if acckey:
                self._store.del_account(acckey)
            else:
                error("account not found.")
        except Exception as e:
            error(f"unable to delete account. Reason:\n    {e}")

    # shortcut
    _delete_acc = _delete_account


    def _delete_transaction(self, args):
        """Delete transaction.
        """
        if len(args) != 1:
            raise Exception("'delete transaction' syntax:\n"
                            "    > del[ete] tr[ansaction] TRANSACTION_ID")
        try:
            self._store.del_transaction(args[0])
        except Exception as e:
            error(f"unable to delete transaction. Reason:\n    {e}")

    # shortcut
    _delete_tr = _delete_transaction


    def _delete_parcel(self, args):
        """Delete parcel.
        """
        if len(args) != 1:
            raise Exception("'delete parcel' syntax\n"
                            "    > del[ete] parcel PARCEL_ID")
        try:
            self._store.del_parcel(args[0])
        except Exception as e:
            error(f"unable to delete parcel. Reason:\n    {e}")


    def _delete_tag(self, args):
        """Delete tag.
        """
        pos, kw, mkw = parse_args(args, 'from')
        if len(pos) != 1 or mkw:
            raise Exception("'delete tag' syntax\n"
                            "    > del[ete] tag TEXT from PARCEL_ID\n"
                            "    > del[ete] tag TEXT")
        try:
            if 'from' in kw:
                self._store.del_parcel_tag(kw['from'], pos[0])
            else:
                self._store.del_tag(pos[0])
        except Exception as e:
            error(f"unable to delete parcel. Reason:\n    {e}")


    def _change_currency(self, args):
        """Change currency settings.
        """
        pos, kw, mkw = parse_args(args, 'short', 'symbol', 'position',
                                        'decplaces', 'decsep')
        if len(pos) != 1 or mkw:
            raise Exception("'change currency' syntax:\n"
                  "    > change curr[ency] NAME [short TEXT] \\\n"
                  "    :                   [symbol TEXT] [position LEFT|RIGHT] \\\n"
                  "    :                   [decplaces NUMBER] [decsep CHARACTER]")
        try:
            curr = self._store.currency(pos[0])
            curr.short_name = kw.get('short', curr.short_name)
            curr.symbol = kw.get('symbol', curr.symbol)
            symb = kw.get('position', curr.symbol_pos).strip().lower()
            if symb not in ('left', 'right'):
                raise ValueError("currency symbol must be 'left' or 'right'.")
            curr.dec_places = parse_number(kw.get('decplaces', curr.dec_places))
            curr.dec_sep = kw.get('decsep', curr.dec_sep)
            self._store.edt_currency(curr)
        except Exception as e:
            error(f"unable to change currency. Reason:\n    {e}")

    # shortcut
    _change_curr = _change_currency


    def _change_account(self, args):
        """Change account.
        """
        pos, kw, mkw = parse_args(args, 'to')
        if (len(pos) != 2 or mkw or 'to' not in kw or 
                (pos[1] not in ('name', 'descr', 'description'))):
            raise Exception("'change account' syntax:\n"
          "    > ch[ange] acc[ount] ACCOUNT_NAME|ACCOUNT_ID name to TEXT\n"
          "    > ch[ange] acc[ount] ACCOUNT_NAME|ACCOUNT_ID descr[iption] to TEXT\n")
        try:
            acc = self._store.account(self._store.account_key(pos[0]))
            if pos[1] == 'name':
                acc.name = kw['to']
            else:
                acc.descr = kw['to']
            self._store.edt_account(acc)
        except Exception as e:
            error(f"unable to change account name. Reason:\n    {e}")

    # shortcut
    _change_acc = _change_account


    def _change_transaction(self, args):
        """Change transaction.
        """
        pos, kw, mkw = parse_args(args, 'to')

        if len(pos) != 2 or 'to' not in kw or mkw or \
                pos[1] not in ('acc', 'account', 'descr', 'description', 'date'):
            raise Exception("'change transaction' syntax:\n"
                  "    > ch[ange] tr[ansaction] TRANSACTION_ID acc[ount] to "
                  "ACCOUNT_NAME|ACCOUNT_ID \n"
                  "    > ch[ange] tr[ansaction] TRANSACTION_ID descr[iption] to TEXT \n"
                  "    > ch[ange] tr[ansaction] TRANSACTION_ID date to DATE")

        try:
            if pos[1] in ('acc', 'account'):
                acckey = self._store.account_key(kw['to'])
                if acckey:
                    self._store.edt_transaction_account(pos[0], acckey)
                else:
                    error("account not found.")
            elif pos[1] in ('descr', 'description'):
                self._store.edt_transaction_descr(pos[0], kw['to'])
            else:  # pos[1] == 'date'
                date = parse_date(kw['to'])
                self._store.edt_transaction_date(pos[0], date)
        except Exception as e:
            error(f"unable to change transaction. Reason:\n    {e}")

    # shortcut
    _change_tr = _change_transaction    


    def _change_parcel(self, args):
        """Change parcel.
        """
        pos, kw, mkw = parse_args(args, 'to')

        if len(pos) != 2 or 'to' not in kw or mkw or \
                 pos[1] not in ('descr', 'description', 'amount'):
            raise Exception("'change parcel' syntax:\n"
                  "    > ch[ange] parcel PARCEL_ID descr[iption] to TEXT\n"
                  "    > ch[ange] parcel PARCEL_ID amount to AMOUNT")
        try:
            if pos[1] in ('descr', 'description'):
                self._store.edt_parcel_descr(pos[0], kw['to'])
            else:   #  pos[1] in ('amount')
                curr = self._store.parcel_currency(pos[0])
                self._store.edt_parcel_amount(pos[0], d2i(kw['to'], curr))
        except Exception as e:
            error(f"unable to change parcel. Reason:\n    {e}")


    def _change_tag(self, args):
        """Change tag.
        """
        pos, kw, mkw = parse_args(args, 'to')
        if len(pos) != 1 or 'to' not in kw or mkw:
            raise Exception("'change tag' syntax:\n"
                            "    > ch[ange] tag TAG to TEXT")
        try:
            self._store.edt_tag(pos[0], kw['to'])
        except Exception as e:
            error(f"unable to change tag. Reason:\n    {e}")


    def _show_manual(self, args):
        """Open the manual in a browser window.
        """
        lenargs = len(args)
        if lenargs > 1 or (lenargs == 1 and args[0] != 'inline'):
            raise Exception("'show manual' syntax:\n.    > show manual [inline]")
        
        if lenargs:
            try:
                data = open(os.path.join(sys.path[0],
                                         'MANUAL.md')).read().splitlines()
                paginate(data=data)
            except Exception as e:
                raise Exception(f"Could not read file. Reason:\n    {e}")
        else:
            webbrowser.open_new(os.path.join(sys.path[0], 'MANUAL.html'))
            print("The program's manual should be displayed in your browser.")
            print("If this doesn't happen, please use the command:\n"
                  "    > show manual inline")
        

    def _show_copyright(self, args):
        """Show copyright information.
        """
        if len(args):
            raise Exception("'show copyright' takes no arguments.")

        print(f"Finance Control {__version__}")
        print(f"(C) {__date__[:4]} {__author__}")
        print(__license__)
        

    def _show_license(self, args):
        """Show program license in a browser window.
        """
        lenargs = len(args)
        if lenargs > 1 or (lenargs == 1 and args[0] != 'inline'):
            raise Exception("'show license' syntax:\n.    > show license [inline]")
        
        if lenargs:
            try:
                data = open(os.path.join(sys.path[0],
                                         'LICENSE.md')).read().splitlines()
                paginate(data=data)
            except Exception as e:
                raise Exception(f"Could not read file. Reason:\n    {e}")
        else:
            webbrowser.open_new(os.path.join(sys.path[0], 'LICENSE.html'))
            print("The program's manual should be displayed in your browser.")
            print("If this doesn't happen, please use the command:\n"
                  "    > show license inline")
        

    def _show_settings(self, args):
        """Show default settings.
        """
        if args:
            raise Exception("'show settings' syntax:\n"
                            "    > sh[ow] settings")
        try:
            data = []
            data.append(f"Prompt: {self._store.metadata('prompt')}")
            data.append(f"Field separator for CSV files: {self._store.metadata('csvsep')}")
            data.append(f"Configured editor: {self._store.metadata('editor')}")
            data.append(f"Default deposit text: {self._store.metadata('deposit')}")
            data.append(f"Default withdrawal text: {self._store.metadata('withdrawal')}")
            data.append(f"Default transfer text: {self._store.metadata('transfer')}")
            data.append(f"Default currency: {self._store.metadata('currency')}")
            paginate(data=data)
        except Exception as e:
            error(f"unable to show settings. Reason:\n    {e}")


    def _show_currency(self, args):
        """Show currency.
        """
        if len(args) != 1:
            raise Exception("'show currency' syntax:\n"
                            "    > sh[ow] curr[ency] CURRENCY_NAME")
        try:
            curr = self._store.currency(args[0])
            data = []
            data.append(f"Name: {curr.name}")
            data.append(f"Short name: {curr.short_name}")
            data.append(f"Symbol: {curr.symbol}")
            data.append(f"Symbol position: {curr.symbol_pos}")
            data.append(f"Decimal places: {curr.dec_places}")
            data.append(f"Decimal separator: {curr.dec_sep}")
            paginate(data=data)
        except Exception as e:
            error(f"unable to show currency. Reason:\n    {e}")

    # shortcut
    _show_curr = _show_currency


    def _show_account(self, args):
        """Show account.
        """
        if len(args) != 1:
            raise Exception("'show account' syntax:\n"
                            "    > sh[ow] acc[ount] ACCOUNT_NAME|ACCOUNT_ID")
        try:
            acc = self._store.account_key(args[0])
            acc = self._store.account(acc)
            curr = self._store.account_currency(acc.key)
            currbal = self._store.account_balance(acc.key, parse_date('today'))
            if currbal:
                currbal = f"{i2d(currbal, curr)}"
            else:
                currbal = '---'
            data = []
            data.append(f"Account ID: {acc.key}")
            data.append(f"Name: {acc.name}")
            data.append(f"Description: {acc.descr}")
            data.append(f"Currency: {curr.name}")
            data.append(f"Balance (current): {i2d(acc.balance, curr)} ({currbal})")
            paginate(data=data)
        except Exception as e:
            error(f"unable to show account information. Reason:\n    {e}")

    # shortcut
    _show_acc = _show_account


    def _show_transaction(self, args):
        """Show transaction.
        """
        if len(args) != 1:
            raise Exception("'show transaction' syntax:\n"
                            "    > sh[ow] tr[ansaction] TRANSACTION_ID")
        try:
            t = self._store.transaction(args[0])
            acc = self._store.transaction_account(t.key)
            curr = self._store.transaction_currency(t.key)
            data= []
            data.append(f"Account: {acc.name} (id: {acc.key})")
            data.append(f"Description: {t.descr}")
            data.append(f"Total amount: {i2d(t.amount, curr)}")
            data.append(f"Date: {t.date}")
            data.append("Parcels:")
            for p in t.parcels:
                amm = i2d(p.amount, curr)
                tags = f" ({', '.join(p.tags)})" if p.tags else ''
                data.append(f"  ({p.key}) {p.descr}: {amm}{tags}")
            paginate(data=data)
        except Exception as e:
            error(f"unable to show transaction. Reason:\n    {e}")

    # shortcut
    _show_tr = _show_transaction


    def _list_currencies(self, args):
        """List currencies.
        """
        pos, kw, mkw = parse_args(args, 'tofile')
        if len(pos) > 1 or mkw:
            raise Exception("'list currencies' syntax:\n"
                            "    > list|ls curr[encies] [NAME] [tofile FILE]")
        try:
            data = [(c.name, c.short_name, c.symbol, c.symbol_pos,
                     str(c.dec_places), c.dec_sep)
                     for c in self._store.currencies(*pos)]
        except Exception as e:
            error(f"unable to list currencies. Reason:\n    {e}")

        headers = ['Name', 'Short name', 'Symbol', 'Position',
                           'Decimal places', 'Decimal separator']
        if 'tofile' in kw:
            export(os.path.expanduser(kw['tofile']), self.csvsep, data, headers)
        else:
            print_table(data, headers)

    # shortcut
    _list_curr = _list_currencies


    def _list_accounts(self, args):
        """List accounts.
        """
        pos, kw, mkw = parse_args(args, 'tofile')
        if len(pos) > 1:
            raise Exception("'list accounts' syntax:\n"
                            "    > list|ls acc[ounts] [ACCOUNT_NAME] [tofile FILE]")
        try:
            data = []
            totals = {}
            for a in self._store.accounts(*pos):
                curr = self._store.account_currency(a.key)
                data.append((str(a.key), a.name, a.descr, i2d(a.balance, curr)))
                totals[curr.name] = totals.get(curr.name, 0) + a.balance
        except Exception as e:
            error(f"unable to list accounts. Reason:\n    {e}")

        headers = ['ID', 'Name', 'Description', 'Balance']
        if 'tofile' in kw:
            export(os.path.expanduser(kw['tofile']), self.csvsep, data, headers)
        else:
            print_table(data, headers, hints='><<>')
            self._totals(totals, 'Total balances by currency')

    # shortcut
    _list_acc = _list_accounts


    def _list_transactions(self, args):
        """List transactions.
        """
        pos, kw, mkw = parse_args(args, 'on', 'from', 'to', 'top', 'tofile')
        if pos or mkw:
            raise Exception("'list transactions' syntax:\n"
                  "    > list|ls tr[ansactions] [on LIST] [from DATE] [to DATE] \\\n"
                  "    :                        [top NUMBER] [tofile FILE]")
        try:
            if 'on' in kw:
                acckey = []
                for acc in kw['on'].split(','):
                    key = self._store.account_key(acc)
                    if not key:
                        raise ValueError("Account not found: {acc}.")
                    acckey.append(key)
            else:
                acckey = None
            datemin = parse_date(kw['from']) if 'from' in kw else None
            datemax = parse_date(kw['to']) if 'to' in kw else None
            if datemin and datemax and datemin > datemax:
                datemin, datemax = datemax, datemin
            limit = parse_number(kw['top']) if 'top' in kw else None
            transactions = self._store.transactions(acckey, datemin, datemax, limit)
            data = []
            totals = {}
            for t in transactions:
                acc = self._store.transaction_account(t.key)
                curr = self._store.transaction_currency(t.key)
                data.append([acc.name, str(t.key), t.date, t.descr,
                             i2d(t.amount, curr), i2d(t.accbalance, curr)])
                totals[curr.name] = totals.get(curr.name, 0) + t.amount
        except Exception as e:
            error(f"unable to list transactions. Reason:\n    {e}")
            return

        headers = ['Account', 'Id', 'Date', 'Description',
                           'Total amount', 'Account balance']
        if 'tofile' in kw:
            export(os.path.expanduser(kw['tofile']), self.csvsep, data, headers)
        else:
            print_table(data, headers, hints='<>><>>')
            self._totals(totals, 'Total amounts by currency')

    # shortcut
    _list_tr = _list_transactions


    def _list_parcels(self, args):
        """List parcels.
        """
        pos, kw, mkw = parse_args(args, 'tagged', 'from', 'to', 'top', 'tofile')
        if pos or mkw or 'tagged' not in kw:
            raise Exception("'list parcels' syntax:\n"
                  "    > list|ls parcels tagged LIST [from DATE] [to DATE] \\\n"
                  "                                  [top NUMBER] [tofile FILE]")

        datemin = parse_date(kw.get('from')) if 'from' in kw else None
        datemax = parse_date(kw.get('to')) if 'to' in kw else None
        if datemin and datemax and datemin > datemax:
            datemin, datemax = datemax, datemin
        limit = parse_number(kw['top']) if 'top' in kw else None
        data = []
        totals = {}
        try:
            for i in self._store.parcels_by_tag(parse_tags(kw['tagged']),
                                                datemin, datemax, limit):
                acc = self._store.transaction_account(i[2])
                curr = self._store.transaction_currency(i[2])
                data.append((str(i[0]), i[1], acc.name, str(i[2]),
                             i[3], i2d(i[4], curr)))
                totals[curr.name] = totals.get(curr.name, 0) + i[4]
        except Exception as e:
            error(f"unable to list parcels by tag. Reason:\n    {e}")

        headers = ['Id', 'Date', 'Account', 'Trans', 'Description', 'Amount']
        if 'tofile' in kw:
            export(os.path.expanduser(kw['tofile']), self.csvsep, data, headers)
        else:
            print_table(data, headers, hints='>><><>')
            self._totals(totals, 'Total amounts by currency')


    def _list_tags(self, args):
        """List tags.
        """
        pos, kw, mkw = parse_args(args, 'tofile')
        if pos or mkw:
            raise Exception("'list tags' syntax:\n"
                            "    > list|ls tags [tofile FILE]")
        try:
            data = [(t[0],str(t[1])) for t in self._store.taglist()]
        except Exception as e:
            error(f"unable to list tags. Reason:\n    {e}")

        headers = ['Tag', 'Frequency']
        if 'tofile' in kw:
            export(os.path.expanduser(kw['tofile']), self.csvsep, data, headers)
        else:
            print_table(data, headers, hints='<>')


    def _find_transactions(self, args):
        """Find transactions by text in their discription.
        """
        pos, kw, mkw = parse_args(args, 'like', 'from', 'to', 'top', 'tofile')
        if pos or mkw:
            raise Exception("'find transactions' syntax:\n"
                  "    > find tr[ransactions] like TEXT [from DATE] [to DATE] \\\n"
                  "    :                                [top NUMBER] [tofile FILE]")

        try:
            datemin = parse_date(kw['from']) if 'from' in kw else None
            datemax = parse_date(kw['to']) if 'to' in kw else None
            if datemin and datemax and datemin > datemax:
                datemin, datemax = datemax, datemin
            limit = parse_number(kw['top']) if 'top' in kw else None
            transactions = \
                self._store.transactions_by_descr(kw['like'], datemin, datemax, limit)
            data = []
            totals = {}
            for t in transactions:
                acc = self._store.transaction_account(t.key)
                curr = self._store.transaction_currency(t.key)
                data.append([acc.name, str(t.key), t.date, t.descr,
                             i2d(t.amount, curr), i2d(t.accbalance, curr)])
                totals[curr.name] = totals.get(curr.name, 0) + t.amount
        except Exception as e:
            error(f"unable to find transactions. Reason:\n    {e}")
            return

        headers = ['Account', 'Id', 'Date', 'Description',
                           'Total amount', 'Account balance']
        if 'tofile' in kw:
            export(os.path.expanduser(kw['tofile']), self.csvsep, data, headers)
        else:
            print_table(data, headers, hints='<>><>>')
            self._totals(totals, 'Total amounts by currency')

    _find_tr = _find_transactions


    def _find_parcels(self, args):
        """Find parcels by text in their discription.
        """
        pos, kw, mkw = parse_args(args, 'like', 'from', 'to', 'top', 'tofile')
        if pos or mkw:
            raise Exception("'find parcels' syntax:\n"
                  "    > find parcels like TEXT [from DATE] [to DATE] \\\n"
                  "    :                        [top NUMBER] [tofile FILE]")

        datemin = parse_date(kw.get('from')) if 'from' in kw else None
        datemax = parse_date(kw.get('to')) if 'to' in kw else None
        if datemin and datemax and datemin > datemax:
            datemin, datemax = datemax, datemin
        limit = parse_number(kw['top']) if 'top' in kw else None
        data = []
        totals = {}
        try:
            for i in self._store.parcels_by_descr(kw['like'],
                                                  datemin, datemax, limit):
                acc = self._store.transaction_account(i[2])
                curr = self._store.transaction_currency(i[2])
                data.append((str(i[0]), i[1], acc.name, str(i[2]),
                             i[3], i2d(i[4], curr)))
                totals[curr.name] = totals.get(curr.name, 0) + i[4]
        except Exception as e:
            error(f"unable to list parcels by description. Reason:\n    {e}")

        headers = ['Id', 'Date', 'Account', 'Trans', 'Description', 'Amount']
        if 'tofile' in kw:
            export(os.path.expanduser(kw['tofile']), self.csvsep, data, headers)
        else:
            print_table(data, headers, hints='>><><>')
            self._totals(totals, 'Total amounts by currency')


    #-------------------------------------------------------------------------
    # Auxilliary methods

    def _editfile(self, fname):
        """Edit a file in an external editor.
        """
        editor = self._store.metadata('editor') if self._store else None 
        if not editor:
            editor = os.environ.get('VISUAL', os.environ.get('EDITOR', ''))

        if editor:
            try:
                subprocess.call([editor, fname])
            except Exception as e:
                error(f"unable to execute the editor. Reason:\n    {e}")
        else:
            error("Could not find an editor to use.\n"
                  "Please choose an editor with the command 'set editor'.")


    def _setdescr(self, cmd, args):
        """Set deposit, withdrawal or transfer description.
        """
        pos, kw, mkw = parse_args(args, 'descr', 'description')
        if pos or ('descr' not in kw and 'description' not in kw):
            raise Exception(f"'set {cmd} description' command syntax:\n"
                            f"    > set {cmd} descr[iption] TEXT")
        try:
            self._store.set_metadata(cmd, kw.get('descr', kw.get('description', '')))
        except Exception as e:
            error(f"unable to set {cmd} description. Reason:\n    {e}")


    def _addtr(self, kw, descr='', parcels=[], mul=1):
        """Add a transaction.
        """
        t = FinStore.Transaction()
        try:
            acc = self._store.account(self._store.account_key(kw['on']))
            curr = self._store.account_currency(acc.key)
            t.account = acc.key
            t.descr = kw.get('descr', kw.get('description', descr))
            t.date = parse_date(kw.get('date', 'today'))
            if not parcels:
                p = FinStore.Parcel()
                p.amount = d2i(kw['of'], curr) * mul
                p.descr = t.descr
                p.tags = parse_tags(kw.get('tags', ''))
                plist = [p]
            else:
                plist = []
                for args in parcels:
                    args = shlex.split(args)
                    ppos, pkw, pmkw = parse_args(args, 'tags')
                    p = FinStore.Parcel()
                    if len(ppos) == 2 and not pmkw:
                        p.descr = ppos[0]
                        p.amount = d2i(ppos[1], curr) * mul
                        p.tags = parse_tags(pkw.get('tags', ''))
                    else:
                        raise ValueError(f"unable to parse parcel: {args}")
                    plist.append(p)
            t.parcels = plist
            self._store.add_transaction(t)
            return t.key
        except Exception as e:
            error(f"unable to add transaction. Reason:\n    {e}")

    
    def _totals(self, totals, title):
        """Print list of totals by currency.
        """
        print(f'{title}:')
        for curr in totals:
            print(f'    {curr}: {i2d(totals[curr], self._store.currency(curr))}')
        print()


