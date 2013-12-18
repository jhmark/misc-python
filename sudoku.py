#!/usr/bin/env python

import argparse
import collections
import logging
import pprint
import re
import sys

import jmutils  # see github.com/jhmark/jmutils

logger = logging.getLogger('sudoku')

Cell = jmutils.Struct('Cell', ('value', 'groups'))
Group = jmutils.Struct('Group', ('name', 'icells', 'contents'))

def lrange(start, stop, step=1):
    return list(range(start, stop, step))

class Puzzle:
    def __init__(self, filename):
        with open(filename) as f:
            vals = re.findall('[\\.0-9]', f.read())
        self.cells = [Cell(None if val == '.' else int(val), [])
                      for val in vals]
        self.groups = self.make_groups()

        self.num_blanks = 0
        for cell in self.cells:
            if cell.value is None:
                self.num_blanks += 1

    def make_groups(self):
        result = []
        for irow in lrange(0, 9):
            icells = lrange(9 * irow, 9 * irow + 9)
            result.append(Group('row%d' % irow, icells, {}))
        for icol in lrange(0, 9):
            icells = lrange(icol, icol + 9*9, 9)
            result.append(Group('col%d' % icol, icells, {}))
        for boxrow in lrange(0, 3):
            for boxcol in lrange(0, 3):
                start = boxrow * 27 + boxcol * 3
                icells = (lrange(start, start + 3) +
                          lrange(start + 9, start + 9 + 3) +
                          lrange(start + 18, start + 18 + 3))
                result.append(Group('box%d' % (boxrow * 3 + boxcol),
                                    icells, {}))

        for group in result:
            for icell in group.icells:
                cell = self.cells[icell]

                # Record in the Cell which groups it is in
                cell.groups.append(group)

                # Record the actual puzzle contents in the Group record
                v = cell.value
                if v is not None:
                    group.contents[v] = True
        return result
    
    def print(self, prompt):
        print('')
        if prompt:
            print(prompt + ':')
        for irow in range(9):
            for icol in range(9):
                c = self.cells[irow * 9 + icol].value
                if c is None:
                    c = '.'
                else:
                    c = repr(c)
                print(c, end='')
                if icol % 3 == 2 and icol < 8:
                    print('|', end='')
            print('')
            if irow % 3 == 2 and irow < 8:
                print('---+---+---')
        print('')

    def search_for_numbers(self):
        for number in range(1, 10):
            for group in self.groups:
                if number in group.contents:
                    continue

                # Found a group that needs NUMBER filled in
                logger.info('trying to add %d to %s' % (number, group.name))
                icell_table = {}
                for icell in group.icells:
                    if self.cells[icell].value is None:
                        icell_table[icell] = True

                # icell_table contains candidate spots
                for icell in sorted(list(icell_table.keys())):
                    logger.info('  checking icell %d' % (icell,))
                    for other_group in self.cells[icell].groups:
                        if other_group is group:
                            continue
                        logger.info('    checking other_group %s' %
                                    (other_group.name,))
                        if number in other_group.contents:
                            # icell cannot contain number
                            logger.info('      rule out icell %d' % (icell,))
                            del icell_table[icell]
                            break
                if len(icell_table) == 1:
                    self.fill_in(list(icell_table.keys())[0], number,
                                 'by seeking %d in %s' % (number, group.name))
                else:
                    logger.info('fail to add %d to %s' % (number, group.name))
                        
    def fill_in(self, icell, number, prompt):
        cell = self.cells[icell]
        assert cell.value is None
        cell.value = number
        self.num_blanks -= 1
        for group in cell.groups:
            group.contents[number] = True
        logger.info('Cell %d = %d ... %s' % (icell, number, prompt))

                
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sudoku solver')
    parser.add_argument('filename')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    logging.basicConfig(stream=sys.stdout,
                        level='DEBUG' if args.debug else 'WARNING')

    p = Puzzle(args.filename)
    p.print('initial (%d blanks)' % (p.num_blanks,))

    iterations = 0
    while True:
        orig_num_blanks = p.num_blanks
        p.search_for_numbers()
        print('search_for_numbers ... %d blanks' % (p.num_blanks,))
        if p.num_blanks in (0, orig_num_blanks):
            break  # no further progress, or done

    p.print('final (%d blanks)' % (p.num_blanks,))
