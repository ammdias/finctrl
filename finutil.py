"""
Finance Control command line interface utility functions
"""

__version__ = '0.5'
__date__ ='2021-10-06'
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
    0.5: Blank input on multiple page listings will advance one page and quit
         on last page
    0.4: Add extra lines for better table visualization;
         paginate() now accepts page number.
    0.3: Corrected bug in d2i() which prevented parsing of decimal numbers
         without leading integer part.
    0.1: Initial version.
"""

import sys
import datetime
import shutil


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


def parse_date(date):
    """Normalize date string.
    """
    if date in ('today', 'now'):
        return datetime.date.today().isoformat()

    try:
        d = tuple(map(int, date.replace('/', '-').split('-')))
        if len(d) == 3:
            month = d[1]
            # check if year is last element, assume it's the first if not
            (year, day) = (d[2], d[0]) if d[2] > 2000 else (d[0], d[2])
            if year < 100:
                year += 2000
        elif len(d) == 2:
            year = datetime.date.today().year
            # check if month is last element, assume it's the first if not
            (day, month) = (d[0], d[1]) if d[0] > 12 else (d[1], d[0])
        else:
            raise ValueError('Could not correctly parse date.')
        date = datetime.date(year, month, day)
    except:
        raise ValueError('Could not correctly parse date.')

    return date.isoformat()


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
    """Returns string representation of integer value with given decimal places. 
    """ 
    neg = '-' if value < 0 else '' 
    value = str(abs(value)) 
    if len(value) > curr.dec_places: 
        i, d = value[:-curr.dec_places], value[-curr.dec_places:] 
    else: 
        i, d = '0', '0' * (curr.dec_places-len(value)) + value 
    return neg + i + curr.dec_sep + d


def d2i(value, curr):
    """Converts float string representation of given decimal places to integer
       with no conversion to float, avoiding float binary representation errors.
    """
    def valid_number(s):
        vd = f'0123456789{curr.dec_sep}'
        for c in s:
            if c not in vd: return False
        return True

    value = value.strip()
    if value[0] == '-':
        mul = -1
        value = value[1:]
    else:
        mul = 1
    if not value or not valid_number(value):
        raise ValueError('Invalid number.')

    value = value.split(curr.dec_sep)
    i, d = (int(value[0]) * 10 ** curr.dec_places) if value[0] else 0, 0
    if len(value) == 2:
        d = int(value[1][:curr.dec_places] + '0' * (curr.dec_places-len(value[1])))

    return (i + d) * mul


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

