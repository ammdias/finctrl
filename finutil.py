"""
Finance Control command line interface utility functions
"""

__version__ = '0.12'
__date__ ='2024-07-31'
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
import datetime
import shutil
import string   # for string.whitespace and string.digits


def yesno(question):
    """Get a yes or no answer to a question.
    """
    answer = ''
    while answer not in ('y', 'yes', 'n', 'no'):
        try:
            answer = input(question + ' (y/n): ').strip().lower()
        except EOFError:
            print('No!')
            break

    return answer in ('y', 'yes')


def parse_number(number):
    """Convert string to a positive integer, if possible.
    """
    if not number.isdecimal() or (n:=int(number)) < 1:
        raise ValueError(f'Invalid number: {number}')

    return n


def parse_date(date):
    """Normalize date string.
    """
    if date in ('today', 'now'):
        return datetime.date.today().isoformat()

    try:
        d = tuple(map(int, date.replace('/', '-').split('-')))
        match len(d):
            case 3:
                month = d[1]
                # check if year is last element, assume it's the first if not
                (year, day) = (d[2], d[0]) if d[2] > 31 else (d[0], d[2])
                if year < 100:
                    year += 2000
            case 2:
                year = datetime.date.today().year
                # check if month is last element, assume it's the first if not
                (day, month) = (d[0], d[1]) if d[0] > 12 else (d[1], d[0])
            case _:
                raise ValueError(f'Invalid date: {date}.')
        date = datetime.date(year, month, day).isoformat()
    except:
        raise ValueError(f'Invalid date: {date}.')

    return date


def parse_args(args, *keywords):
    """Parse a list of arguments, dividing it in a list of postional arguments,
       a dictionary of keyword arguments and another of multiple keyword arguments.
    """
    pos, kw, mkw = [], {}, {}
    while args:
        a = args.pop(0)
        if a in keywords:
            if not args:
                raise ValueError(f"keyword argument without value: {a}")
            if a in kw:
                mkw[a] = [kw[a], args.pop(0)]
                del kw[a]
            elif a in mkw:
                mkw[a].append(args.pop(0))
            else:
                kw[a] = args.pop(0)
        else:
            pos.append(a)

    return (pos, kw, mkw)


def parse_tags(tags):
    """Return list of tags.
    """
    return [t.strip() for t in tags.split(',')] if tags.strip() else []


def i2d(value, curr): 
    """Returns string representation of integer value according to currency
       decimal places.
    """ 
    result = '{c} {v}' if curr.symbol_pos == 'left' else '{v} {c}'
    sign = '-' if value < 0 else '' 
    ival, dval = divmod(abs(value), 10 ** curr.dec_places)
    value = f"{sign}{ival}{curr.dec_sep}{dval:0{curr.dec_places}}"

    return result.format(c=curr.symbol, v=value)


def d2i(value, curr):
    """Converts float string representation of currency to number with no
       decimal places, avoiding float binary representation errors.
    """
    def valid_number(s):
        valid_digits = string.digits + curr.dec_sep
        for c in (s[1:] if s[0] in '-+' else s):
            if c not in valid_digits:
                return False

        if value.count(curr.dec_sep) > 1: # no multiple decimal separators
            return False

        return True

    # remove currency symbol and whitespace from start/end of value
    value = value.strip(curr.symbol + string.whitespace)

    if not value or not valid_number(value):
        raise ValueError('Invalid number.')

    ival, _, dval = value.partition(curr.dec_sep)
    return int(ival + dval.ljust(curr.dec_places, '0')[:curr.dec_places])


def print_table(data, headers=[], hints=None):
    """Print a table on screen.
    """
    if not data:
        raise ValueError("Empty set")

    def max_col_sizes(): 
        res = [len(i) for i in headers] if headers else [0] * len(data[0]) 
        for ln in data: 
            for i,cell in enumerate(ln): 
                if len(cell) > res[i]: 
                    res[i] = len(cell) 
        return res 

    colsep = ' | '
    headsep, headcolsep = '-', '-+-'
    sizes = max_col_sizes()
    hints = hints if hints else '<' * len(sizes)

    pageheader = []
    if headers:
        headln = []
        for idx,col in enumerate(headers):
            headers[idx] = f"{col:<{sizes[idx]}s}"
            headln.append(headsep * sizes[idx])
        pageheader = [colsep.join(headers), headcolsep.join(headln)]

    pagedata = []
    for row in data:
        pagedata.append(colsep.join([f"{col:{hints[idx]}{sizes[idx]}s}"
                                     for idx,col in enumerate(row)]))
    print()
    paginate(pageheader, pagedata)
    

def paginate(header=[], data=[]):
    """Print data split by pages accounting for screen size.
    """
    footer = "Page {} of {}. (N)ext / (P)revious / Page number / (Q)uit ? "
    term_width, term_height = shutil.get_terminal_size()
    page_size = term_height - len(header) - 2 # 2: len of footer

    def println(line):
        if len(line) < term_width:
            print(line)
        else:
            print(line[:term_width - 4] + ' ...')

    def print_page(page_num):
        for i in header:
            println(i)
        for i in data[page_num*page_size:(page_num+1)*page_size]:
            println(i)
        print()

    if len(data) <= page_size:
        print_page(0)
    else:
        pages = len(data) // page_size + (len(data) % page_size != 0)
        page, cmd = 0, ''
        while cmd not in ('q', 'quit'):
            print_page(page)
            try:
                cmd = input(footer.format(page+1, pages)).strip().lower()
            except EOFError:
                print('Quit!')
                break;
            if cmd in ('n', 'next', '') and page < pages-1:
                page += 1
            elif cmd in ('p', 'previous') and page > 0:
                page -= 1
            elif cmd.isdigit():
                pagenum = int(cmd)
                if 0 < pagenum <= pages:
                    page = pagenum - 1
            elif cmd == '' and page == pages - 1:
                break
            print()


def export(filepath, csvsep, data, headers=[]):
    """Export data to CSV file.
    """
    try:
        with open(filepath, 'w') as f:
            if headers:
                print(csvsep.join(headers), file=f)
            for row in data:
                print(csvsep.join(row), file=f)
    except Exception as e:
        raise Exception(f"unable to write to file. Reason:\n    {e}")


def error(msg):
    """Display error message.
    """
    print(f'*** Error: {msg}\n', file=sys.stderr)

