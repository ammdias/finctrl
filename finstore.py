"""
FinStore: class to store finance control data in a sqlite3 database.
"""

__version__ = '0.1'
__date__ = '2021-02-18'  # TODO: Change!
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

from sqlitestore import SQLiteStore


#-----------------------------------------------------------------------------
# The FinStore class

class FinStore(SQLiteStore):
    """Describe and store FinCtrl data in a SQLite3 storage file.
    """
    
    class Currency:
        (name, short_name,
         symbol, symbol_pos, dec_places, dec_sep) = (None, '',
                                                    '', 'left', 2, '.' )
        def __init__(self, *params):
            if len(params):
                (self.name, self.short_name, self.symbol, self.symbol_pos,
                            self.dec_places, self.dec_sep) = params

    class Account:
        key, name, balance, descr, currency = (None, '', 0, '', '')
        def __init__(self, *params):
            if len(params):
                (self.key, self.name, self.balance,
                 self.descr, self.currency) = params

    class Transaction:
        key, account, date, descr, amount, accbalance = (None, None, '', '', 0, 0)
        def __init__(self, *params):
            if len(params):
                (self.key, self.account, self.date, self.descr,
                 self.amount, self.accbalance) = params
            self.parcels = []

    class Parcel:
        key, trans, descr, amount = (None, None, '', 0)
        def __init__(self, *params):
            if len(params):
                (self.key, self.trans, self.descr, self.amount) = params
            self.tags = []

    #--------------------------------------------------------------------------

    def __init__(self, storepath, create=False, **metadata):
        """Connect to database creating it if required and necessary.
           Set metadata in database.
        """
        SQLiteStore.__init__(self, storepath, create, **metadata)
        with self._db:
            if create:
                self._script(_SCRIPT_CREATE)


    def add_currency(self, currency):
        """Insert currency in the database.
        """
        c = self._do("insert into currencies values(?,?,?,?,?,?)",
                     (currency.name, currency.short_name,
                      currency.symbol, currency.symbol_pos,
                      currency.dec_places, currency.dec_sep))


    def edt_currency(self, currency):
        """Change currency values.
        """
        if not self._exists('currencies', 'name', currency.name):
            raise ValueError("Currency not found.")

        self._do("update currencies set short_name=?, symbol=?, symbol_pos=?, "
                 "dec_places=?, dec_sep=? where name=?",
                 (currency.short_name, currency.symbol, currency.symbol_pos,
                  currency.dec_places, currency.dec_sep, currency.name))


    def currency(self, currname):
        """Return currency with name currname.
        """
        curr = self._qry("select * from currencies where name like ?",
                         (currname,))
        if len(curr) == 0:
            raise ValueError("Currency not found.")
        if len(curr) > 1:
            raise ValueError("Multiple currencies satisfy criteria.")

        return self.Currency(*curr[0])


    def currencies(self, name=None):
        """Return list of currencies.
        """
        if name:
            qry = ("select * from currencies where name like ?", (name,))
        else:
            qry = ("select * from currencies",)

        return [self.Currency(*curr) for curr in self._qry(*qry)]


    def add_account(self, account):
        """Insert account in the database.
        """
        if not account.name:
            raise ValueError("Account must have a name.")

        c = self._do("insert into accounts values(null,?,?,?,?)",
                      (account.name, account.balance, account.descr,
                       account.currency))
        account.key = c.lastrowid


    def edt_account(self, account):
        """Change account data.
        """
        if not self._exists('accounts', 'key', account.key):
            raise ValueError("Account not found.")

        self._do("update accounts set name=?, descr=? where key=?",
                 (account.name, account.descr, account.key))


    def del_account(self, acckey):
        """Remove account with key acckey.
        """
        self._do("delete from accounts where key=?", (acckey,))


    def account(self, acckey):
        """Return account with key acckey.
        """
        acc = self._qry1("select * from accounts where key=?", (acckey,))
        if not acc:
            raise ValueError("Account not found.")

        return self.Account(*acc)


    def accounts(self, name=None):
        """Return list of accounts.
        """
        if name:
            qry = ("select * from accounts where name like ?", (name,))
        else:
            qry = ("select * from accounts",)

        return [self.Account(*acc) for acc in self._qry(*qry)]


    def account_key(self, key_or_name):
        """Return account key given a key or name.
        """
        if self._exists('accounts', 'key', key_or_name):
            return key_or_name

        res = self._qry("select key from accounts where name like ?",
                        (key_or_name,))
        if len(res) > 1:
            raise ValueError("Multiple accounts satisfy criteria.")
        
        return res[0][0] if res else None


    def account_currency(self, acckey):
        """Return the currency of an account.
        """
        if not self._exists('accounts', 'key', acckey):
            raise Exception("Account not found.")

        curr = self._qry1("select C.* from accounts as A, currencies as C "
                          "where A.key=? and C.name=A.currency", (acckey,))
 
        return self.Currency(*curr) if curr else None


    def account_balance(self, acckey, date):
        """Return account balance at specified date.
        """
        if not self._exists('accounts', 'key', acckey):
            raise ValueError("Acccount not found.")

        bal = self._qry1("select accbalance from transactions "
                          "where account=? and date<=? "
                          "order by date desc, key desc limit 1", (acckey, date))

        return bal[0] if bal else None


    def _upd_account_balance(self, acckey):
        """Update account balance after transaction modifications.
        """
        self._exec("update accounts "
                   "set balance=(select accbalance from transactions "
                   "             where account=? "
                   "             order by date desc, key desc limit 1) "
                   "where key=?", (acckey, acckey))


    def trim(self, date, acckey=None):
        """Remove all transactions up to date.
        """
        accounts = [acckey] if acckey else \
                   [i[0] for i in self._qry("select key from accounts")]

        for a in accounts:
            self._do("delete from transactions where account=? and date<=?",
                     (a, date))
            # check if all transactions were deleted
            if not self._qry1("select count() from transactions where account=?",
                              (a,))[0]:
                t = self.Transaction()
                t.account = a
                t.date = date
                t.descr = "Trim carry-over"
                amm = self._qry1("select balance from accounts where key=?", (a,))[0]
                t.parcels = [self.Parcel(None, 0, "Trim carry-over", amm)]
                self.add_transaction(t)


    def add_transaction(self, transaction):
        """Insert transaction in database.
        """
        with self._db:
            accbal = self._get_trans_accbalance(transaction.account,
                                                transaction.date)
            c = self._exec("insert into transactions values(null,?,?,?,0,?)",
                           (transaction.account, transaction.date,
                            transaction.descr, accbal))
            transaction.key = c.lastrowid

            for p in transaction.parcels:
                p.trans = transaction.key
                c = self._exec("insert into parcels values(null,?,?,?)",
                               (p.trans, p.descr, p.amount))
                p.key = c.lastrowid
                for t in p.tags:
                    self._exec("insert into parceltags values(?,?)", (p.key, t))

            total = self._qry1("select sum(amount) from parcels "
                               "where trans=?", (transaction.key,))[0]
            self._exec("update transactions set amount=? "
                       "where key=?", (total, transaction.key))
            self._upd_trans_accbalance(transaction.key, transaction.account,
                                       total, transaction.date)


    def edt_transaction_descr(self, transkey, descr):
        """Change transaction description.
        """
        if not self._exists("transactions", "key", transkey):
            raise ValueError("Transaction not found.")

        self._do("update transactions set descr=? where key=?",
                 (descr, transkey))


    def edt_transaction_account(self, transkey, acckey):
        """Change transaction account.
        """
        t = self.transaction(transkey)
        if not t:
            raise ValueError("Transaction not found.")
        if not self._exists("accounts", "key", acckey):
            raise ValueError("Account not found.")

        self.del_transaction(transkey)
        t.key, t.account, t.accbalance = None, acckey, 0
        self.add_transaction(t)


    def edt_transaction_date(self, transkey, date):
        """Change transaction date.
        """
        t = self._qry1("select date, account, amount from transactions "
                       "where key=?", (transkey,))
        if not t:
            raise ValueError("Transaction not found.")
        oldate, acckey, amount = t

        with self._db:
            self._upd_trans_accbalance(transkey, acckey, -amount, oldate)
            accbal = self._get_trans_accbalance(acckey, date, transkey)
            self._exec("update transactions set date=?, accbalance=? "
                       "where key=?",
                       (date, accbal, transkey))
            self._upd_trans_accbalance(transkey, acckey, amount, date)


    def del_transaction(self, transkey):
        """Remove transaction with key transkey.
        """
        t = self._qry1("select account, amount, date "
                       "from transactions where key=?", (transkey,))
        if not t:
            raise ValueError("Transaction not found.")
        with self._db:
            self._exec("delete from transactions where key=?", (transkey,))
            self._upd_trans_accbalance(transkey, t[0], t[1], t[2])


    def transaction(self, transkey):
        """Return transaction with key transkey.
        """
        t = self._qry1("select * from transactions where key=?", (transkey,))
        if not t:
            raise ValueError("Transaction not found.")
        t = self.Transaction(*t)
        t.parcels = self.parcels_by_transaction(t.key)
        return t


    def transactions(self, acckey=None, datemin=None, datemax=None, limit=None):
        """Return list of transactions.
        """
        conds, params = [], []
        if acckey:
            conds.append("account=?")
            params.append(acckey)
        if datemin:
            conds.append("date>=?")
            params.append(datemin)
        if datemax:
            conds.append("date<=?")
            params.append(datemax)

        cond = f"where {' and '.join(conds)}" if conds else ''
        lim = f"limit {int(limit)}" if limit else ''

        return [self.Transaction(*t)
                for t in self._qry(f"select * from transactions {cond} "
                    f"order by account, date desc, key desc {lim}",
                                   tuple(params))]


    def transaction_account(self, transkey):
        """Return account of a transaction.
        """
        if not self._exists('transactions', 'key', transkey):
            raise ValueError("Transaction not found.")

        acc = self._qry1("select A.* from accounts as A, transactions as T "
                         "where T.key=? and A.key=T.account", (transkey,))
        
        return self.Account(*acc) if acc else None


    def transaction_currency(self, transkey):
        """Return the currency of a transaction.
        """
        if not self._exists('transactions', 'key', transkey):
            raise Exception("Transaction not found.")

        curr = self._qry1("select C.* "
                          "from transactions as T, accounts as A, currencies as C "
                          "where T.key=? and A.key=T.account and C.name=A.currency",
                          (transkey,))
 
        return self.Currency(*curr) if curr else None


    def _get_trans_accbalance(self, acckey, date, transkey=None):
        """Get account balance on a specific date and transaction order.
        """
        # multiple transactions on same date, accbalance is accbalance of
        # transaction with highest transaction key less than transkey
        if transkey and self._qry1("select count() from transactions "
                                   "where account=? and date=?",
                                   (acckey, date))[0]:
            accbal = self._qry1("select accbalance from transactions "
                                "where key<? and account=? and date=? "
                                "order by date desc, key desc limit 1",
                                (transkey, acckey, date))

        # first transaction at date, accbalance is accbalance from
        # transaction with highest key and date less than date
        else:
            accbal = self._qry1("select accbalance from transactions "
                                "where account=? and date<=? "
                                "order by date desc, key desc limit 1",
                                (acckey, date))

        return accbal[0] if accbal else 0


    def _upd_trans_accbalance(self, transkey, acckey, amount, date):
        """Update transactions account balances after a transaction modification.
        """
        self._exec("update transactions set accbalance=accbalance+? "
                   "where date=? and key>=? and account=?",
                   (amount, date, transkey, acckey))
        self._exec("update transactions set accbalance=accbalance+? "
                   "where date>? and account=?",
                   (amount, date, acckey))
        self._upd_account_balance(acckey)


    def add_parcel(self, parcel):
        """Insert a parcel.
        """
        t = self._qry1("select key, account, date from transactions "
                       "where key=?", (parcel.trans,))
        if not t:
            raise ValueError("Transaction not found.")
        transkey, acckey, date = t
        with self._db:
            c = self._exec("insert into parcels values(null,?,?,?)",
                           (parcel.trans, parcel.descr, parcel.amount))
            parcel.key = c.lastrowid
            for t in parcel.tags:
                self._exec("insert into parceltags values(?, ?)",
                           (parcel.key, t))
            self._exec("update transactions set amount=amount+? "
                       "where key=?", (parcel.amount, parcel.trans))
            self._upd_trans_accbalance(transkey, acckey, parcel.amount, date)


    def edt_parcel_descr(self, parcelkey, descr):
        """Change parcel description.
        """
        if not self._exists("parcels", "key", parcelkey):
            raise ValueError("Parcel not found.")
        self._do("update parcels set descr=? where key=?", (descr, parcelkey,))


    def edt_parcel_amount(self, parcelkey, amount):
        """Change parcel amount.
        """
        p = self._qry1("select trans, amount from parcels where key=?",
                       (parcelkey,))
        if not p:
            raise ValueError("Parcel not found.")
        transkey, oldamm = p
        acckey, date = self._qry1("select account, date from transactions "
                                  "where key=?", (transkey,))
        with self._db:
            self._exec("update parcels set amount=? where key=?",
                       (amount, parcelkey,))
            self._exec("update transactions set amount=amount+? "
                       "where key=?", (amount-oldamm, transkey))
            self._upd_trans_accbalance(transkey, acckey, amount-oldamm, date)


    def del_parcel(self, parcelkey):
        """Remove parcel.
        """
        p = self._qry1("select trans, amount from parcels where key=?",
                       (parcelkey,))
        if not p:
            raise ValueError("Parcel not found.")
        transkey, amount = p
        acckey, date = self._qry1("select account, date from transactions "
                                  "where key=?", (transkey,))
        with self._db:
            self._exec("delete from parcels where key=?", (parcelkey,))
            self._exec("update transactions set amount=amount-? "
                       "where key=?", (amount, transkey))
            self._upd_trans_accbalance(transkey, acckey, -amount, date)


    def add_parcel_tag(self, parcelkey, tag):
        """Add tag to a parcel.
        """
        if not self._exists("parcels", "key", parcelkey):
            raise ValueError("Parcel not found.")
        self._do("insert into parceltags values (?, ?)", (parcelkey, tag))


    def del_parcel_tag(self, parcelkey, tag):
        """Remove tag from a parcel.
        """
        self._do("delete from parceltags where parcel=? and tag=?",
                 (parcelkey, tag))


    def parcel(self, parcelkey):
        """Return parcel with key parcelkey.
        """
        p = self._qry1("select * from parcels where key=?", (parcelkey,))
        if p:
            p = self.Parcel(*p)
            self.fill_tags([p])
        return p


    def parcels(self, datemin=None, datemax=None, limit=None):
        """Return list of parcels according to preset conditions.
        """
        conds, params = [], []
        if datemin:
            conds.append("T.date>=?")
            params.append(datemin)
        if datemax:
            conds.append("T.date<=?")
            params.append(datemax)

        conds = "and " + " and ".join(conds) if conds else ''
        lim = f"limit {int(limit)}" if limit else ''

        plist = [self.Parcel(*p)
                 for p in self._qry("select P.* "
                                    "from transactions as T, parcels as P "
                                    f"where P.trans=T.key {conds} "
                                    f"group by T.key order by T.date desc, P.key {lim}",
                                    tuple(params))]
        self.fill_tags(plist)

        return plist


    def parcels_by_transaction(self, transaction):
        """Return list of parcels in a transaction.
        """
        plist = [self.Parcel(*p)
                 for p in self._qry("select * from parcels where trans=?",
                                     (transaction,))]
        self.fill_tags(plist)

        return plist


    def parcels_by_tag(self, tags, datemin=None, datemax=None, limit=0):
        """Return parcels by tag according to conditions.
        """
        if not tags or type(tags)!=list:
            raise ValueError("tags is not a non-empty list of tags.")

        cond, params = [], tags
        tagcond = '(' + 'or '.join(["PT.tag like ?"] * len(tags)) + ')'

        if datemin:
            cond.append("T.date>=?")
            params.append(datemin)
        if datemax:
            cond.append("T.date<=?")
            params.append(datemax)

        cond = "and " + " and ".join(cond) if cond else ''
        lim = f"limit {int(limit)}" if limit else ''

        return self._qry(
                "select distinct P.key, T.date, T.key, P.descr, P.amount "
                "from transactions as T, parcels as P, parceltags as PT "
                f"where PT.parcel=P.key and P.trans=T.key and {tagcond} {cond} "
                f"order by T.date desc, T.key desc, P.key {lim}",
                         tuple(params))


    def parcel_account(self, parcelkey):
        """Return account of a parcel.
        """
        if not self._exists('parcels', 'key', parcelkey):
            raise ValueError("Parcel not found.")

        acc = self._qry1("select A.* "
                         "from accounts as A, transactions as T, parcels as P  "
                         "where P.key=? and T.key=P.trans and A.key=T.account",
                         (parcelkey,))
        
        return self.Account(*acc) if acc else None


    def parcel_currency(self, parcelkey):
        """Return currency of a parcel.
        """
        if not self._exists('parcels', 'key', parcelkey):
            raise ValueError("Parcel not found.")

        curr = self._qry1("select C.* from parcels as P, transactions as T, "
                          "                accounts as A, currencies as C "
                          "where P.key=? and T.key=P.trans and "
                          "      A.key=T.account and C.name=A.currency",
                          (parcelkey,))
 
        return self.Currency(*curr) if curr else None


    def edt_tag(self, oldtag, newtag):
        """Change a tag name.
        """
        self._do("update parceltags set tag=? where tag=?", (newtag, oldtag))


    def del_tag(self, tag):
        """Delete a tag.
        """
        self._do("delete from parceltags where tag=?", (tag,))


    def taglist(self):
        """Return list of unique tags.
        """
        return self._qry("select T,(select count() from parceltags where tag=T) "
                         "from (select distinct tag as T from parceltags)")


    def tags_by_parcel(self, parcel):
        """Return list of tags by parcel.
        """
        return [t[0]
                for t in self._qry("select tag from parceltags where parcel=?",
                                   (parcel,))]


    def fill_tags(self, parcel_list):
        """Fill tags parameter in a parcel list.
        """
        for p in parcel_list:
            p.tags = self.tags_by_parcel(p.key)


#-----------------------------------------------------------------------------
# The SQL script to create sqlite storage

_SCRIPT_CREATE = """
create table currencies (
    name        text not null,
    short_name  text,
    symbol      text,
    symbol_pos  text,
    dec_places  integer,
    dec_sep     text,
    primary key (name)
);

insert into currencies values('default', '', '', 'left', 2, '.');

create table accounts (
    key         integer,
    name        text not null,
    balance     integer,
    descr       text,
    currency    text,
    primary key (key),
    foreign key (currency) references currencies(name)
);
 
create table transactions (
    key         integer,
    account     integer not null,
    date        text,
    descr       text,
    amount      integer not null,
    accbalance  integer not null,
    primary key (key),
    foreign key (account) references accounts(key)
);

create table parcels (
    key         integer,
    trans       integer not null,
    descr       text,
    amount      integer not null,
    primary key (key),
    foreign key (trans) references transactions(key)
);

create table parceltags (
    parcel      integer not null,
    tag         text not null,
    primary key (parcel, tag),
    foreign key (parcel) references parcels(key)
);

create trigger del_currency before delete on currencies
begin
    delete from accounts where currency=old.name;
end;

create trigger del_account before delete on accounts
begin
    delete from transactions where account=old.key;
end;

create trigger del_transaction before delete on transactions
begin
    delete from parcels where trans=old.key;
end;

create trigger del_parcel after delete on parcels
begin
    delete from parceltags where parcel=old.key;
end;
"""
