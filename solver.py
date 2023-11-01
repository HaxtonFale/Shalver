import argparse
import logging
from enum import StrEnum
from typing import List, Self, Tuple

from termcolor import colored

import shallie
from atelier_types import Category, Item

log = logging.getLogger('solver')
log.setLevel(logging.INFO)

c_handler = logging.StreamHandler()
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
log.addHandler(c_handler)

shallie.load_data()

class StepType(StrEnum):
    Synthesize  = 'Synthesize'
    SynthAsCat  = 'Synthesize as Category'
    Disassemble = 'Disassemble'

class Solution:
    max_depth = 10

    def __init__(self, current_item: Item, next_step: Tuple[Self, StepType, Category | None] | None = None) -> None:
        self.current_item = current_item
        self.next_step = next_step
        self.depth = 1
        if self.next_step is not None:
            self.depth += self.next_step[0].depth
        if Solution.max_depth > 0 and self.depth > Solution.max_depth:
            raise ValueError(f'Solution depth limit ({Solution.max_depth}) exceeded')

    def add_step(self, new_item: Item, next_step_type: StepType, next_step_category: Category | None = None) -> Self:
        return Solution(new_item, (self, next_step_type, next_step_category))

    def print_solution(self, step: int = 1) -> str:
        if self.next_step is None:
            return 'Done.'
        else:
            next_step, step_type, category = self.next_step
            match step_type:
                case StepType.Synthesize:
                    output = f'Synthesise {colored(str(next_step.current_item), 'green')} with {colored(str(self.current_item), 'blue')}.'
                case StepType.SynthAsCat:
                    assert category is not None
                    output = f'Synthesise {colored(str(next_step.current_item), 'green')} with {colored(str(self.current_item), 'yellow')} as {colored(str(category), 'blue')}.'
                case StepType.Disassemble:
                    output = f'Disassemble {colored(str(next_step.current_item), 'green')} into {colored(str(self.current_item), 'blue')}'
            return f'{step}. ' + output + '\n' + next_step.print_solution(step + 1)

    def __repr__(self) -> str:
        return f'Partial solution for {self.current_item} [{self.depth} step(s)]'


def find_solution(added_item: Item, destination_item: Item, max_depth: int) -> Solution:
    Solution.max_depth = max_depth

    solutions: List[Solution] = list()
    solutions.append(Solution(destination_item))

    def add_solution(solution: Solution) -> None:
        ingredient = solution.current_item
        if shallie.has_recipe(ingredient):
            log.debug('Partial solution found. Adding to solutions queue.')
            solutions.append(solution)
        else:
            log.debug('Not a craftable item.')

    while len(solutions) > 0:
        solution = solutions.pop(0)
        log.debug('Finding ingredients for %s...', solution.current_item)
        ingredients = shallie.get_ingredients(solution.current_item)
        log.debug('Found ingredients: %s', ', '.join([str(ing) for ing in ingredients]))
        for ingredient in ingredients:
            try:
                log.debug('Testing ingredient %s', ingredient)
                if isinstance(ingredient, Item):
                    log.debug('Ingredient identified as Item.')
                    new_solution = solution.add_step(ingredient, StepType.Synthesize)
                    if ingredient is added_item:
                        log.debug('Complete solution found!')
                        return new_solution
                    else:
                        add_solution(new_solution)
                elif isinstance(ingredient, Category):
                    log.debug('Ingredient identified as category.')
                    category_items = shallie.get_category_items(ingredient)
                    for cat_item in category_items:
                        log.debug('Testing ingredient %s', cat_item)
                        new_solution = solution.add_step(cat_item, StepType.SynthAsCat, ingredient)
                        if cat_item is added_item:
                            log.debug('Complete solution found!')
                            return new_solution
                        else:
                            add_solution(new_solution)
            except ValueError:
                continue
        log.debug('Checking Disassembly options...')
        disassemblies = shallie.get_disassemblies(solution.current_item)
        log.debug('Found %i disassemblies', len(disassemblies))
        for disassembly in disassemblies:
            try:
                new_solution = solution.add_step(disassembly.source_item, StepType.Synthesize)
                if disassembly.source_item is added_item:
                    return new_solution
                else:
                    add_solution(new_solution)
            except ValueError:
                continue

    raise StopIteration('No solution found')

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--source', help='Item added to the recipe; source of a trait', choices=shallie.get_item_names(), type=str)
parser.add_argument('-d', '--destination', help='Final recipe; destination of a trait', choices=shallie.get_recipe_names(), type=str)
parser.add_argument('--depth', help='Maximum search depth. 0 for infinity.', type=int, default=10)
parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')

args = parser.parse_args()
if args.verbose:
    log.setLevel(logging.DEBUG)

src_item = shallie.get_item(args.source)
dst_item = shallie.get_item(args.destination)

print(f'Attempting to find a synthesis path from {colored(str(src_item), 'blue')} to {colored(str(dst_item), 'green')}')
print(find_solution(src_item, dst_item, args.depth).print_solution())