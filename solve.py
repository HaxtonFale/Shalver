import argparse
import logging

from termcolor import colored

import shallie
from solver import Solution, find_solution_bfs

log = logging.getLogger('solve')
log.setLevel(logging.INFO)

c_handler = logging.StreamHandler()
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
log.addHandler(c_handler)

shallie.load_data(log)

src_items = shallie.get_item_names(shallie.get_trait_donors())
dst_items = shallie.get_item_names(shallie.get_trait_recipients())

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--source', help='Item added to the recipe; source of a trait',
                    choices=src_items, type=str)
parser.add_argument('-d', '--destination', help='Final recipe; destination of a trait',
                    choices=dst_items, type=str)
parser.add_argument('--depth', help='Maximum search depth. 0 for infinity.', type=int, default=0)
parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')

args = parser.parse_args()
if args.verbose:
    log.setLevel(logging.DEBUG)

src_item = shallie.get_item(args.source)
dst_item = shallie.get_item(args.destination)

print(f'Attempting to find a synthesis path from {colored(str(src_item), 'blue')} ' +
    f'to {colored(str(dst_item), 'green')}')
Solution.max_depth = args.depth
solution = find_solution_bfs(log, src_item, dst_item, shallie.get_ingredients,
                                shallie.get_category_items, shallie.has_recipe,
                                shallie.get_disassembly_sources)
if solution is None:
    print(colored('No valid solution found.', 'red'))
else:
    print(solution.print_solution())