import argparse
import logging
from collections import namedtuple
from typing import List

from termcolor import colored

import shallie
from solver import find_solution_bfs

log = logging.getLogger('find_longest')
log.setLevel(logging.INFO)

c_handler = logging.StreamHandler()
c_format = logging.Formatter('[%(levelname)s|%(name)s] %(asctime)s - %(message)s')
c_handler.setFormatter(c_format)
log.addHandler(c_handler)

shallie.load_data(log)

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')

args = parser.parse_args()
if args.verbose:
    log.setLevel(logging.DEBUG)

log.info('Finding the longest solution available...')
src_items = shallie.get_trait_donors()
dst_items = shallie.get_trait_recipients()
log.info('There are %i donor items and %i recipient items.', len(src_items), len(dst_items))

SolutionSpec = namedtuple('SolutionSpec', ['solution', 'donor', 'recipient'])

solutions: List[SolutionSpec] = list()
longest_length: int = 0

for src in src_items:
    for dst in dst_items:
        log.debug('Testing %s -> %s', colored(str(src), 'blue'), colored(str(dst), 'green'))
        solution = find_solution_bfs(log, src, dst, shallie.get_ingredients,
                                     shallie.get_category_items, shallie.has_recipe,
                                     shallie.get_disassembly_sources)
        if solution is None:
            log.debug('No solution found.')
            continue
        log.debug('Valid solution found (%i steps).', len(solution))
        spec = SolutionSpec(solution, src, dst)
        solutions.append(spec)
        longest_length = max(longest_length, len(solution))

longest_solutions: List[SolutionSpec] = [spec for spec in solutions if len(spec.solution) == longest_length]

log.info('Found %i valid solutions, of which %i are the longest (%i steps):', len(solutions), len(longest_solutions), longest_length)
for _, src, dst in longest_solutions:
    log.info('From %s to %s', colored(str(src), 'blue'), colored(str(dst), 'green'))