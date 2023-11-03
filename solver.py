from enum import StrEnum
from logging import Logger
from typing import Callable, List, Self, Set, Tuple

from termcolor import colored

from atelier_types import Category, Item

class StepType(StrEnum):
    Synthesize  = 'Synthesize'
    SynthAsCat  = 'Synthesize as Category'
    Disassemble = 'Disassemble'

SolutionStep = Tuple['Solution', StepType, Category | None]

class Solution:
    max_depth = 0

    def __init__(self, current_item: Item,
                 next_step: SolutionStep | None = None) -> None:
        self.current_item = current_item
        self.next_step = next_step
        self.depth = 1
        if self.next_step is not None:
            self.depth += self.next_step[0].depth
        if Solution.max_depth > 0 and self.depth > Solution.max_depth:
            raise ValueError(f'Solution depth limit ({Solution.max_depth}) exceeded')

    def add_step(self, new_item: Item, next_step_type: StepType,
                 next_step_category: Category | None = None) -> Self:
        return Solution(new_item, (self, next_step_type, next_step_category))

    def print_solution(self, step: int = 1) -> str:
        if self.next_step is None:
            return 'Done.'
        else:
            next_step, step_type, category = self.next_step
            match step_type:
                case StepType.Synthesize:
                    output = (f'Synthesise {colored(str(next_step.current_item), 'green')} ' +
                              f'with {colored(str(self.current_item), 'blue')}.')
                case StepType.SynthAsCat:
                    assert category is not None
                    output = (f'Synthesise {colored(str(next_step.current_item), 'green')} ' +
                              f'with {colored(str(self.current_item), 'yellow')} ' +
                              f'as {colored(str(category), 'blue')}.')
                case StepType.Disassemble:
                    output = (f'Disassemble {colored(str(next_step.current_item), 'green')} ' +
                              f'into {colored(str(self.current_item), 'blue')}')
            return f'{step}. ' + output + '\n' + next_step.print_solution(step + 1)

    def __repr__(self) -> str:
        return f'Partial solution for {self.current_item} [{self.depth} step(s)]'

    def __len__(self) -> int:
        return self.depth

def find_solution_bfs(log: Logger, added_item: Item, destination_item: Item,
                      get_ingredients: Callable[[Item], List[Category | Item]],
                      get_category_items: Callable[[Category], List[Item]],
                      has_recipe: Callable[[Item], bool],
                      get_disassembly_sources: Callable[[Item], List[Item]] | None = None) -> Solution | None:
    solutions: List[Solution] = list()
    solutions.append(Solution(destination_item))

    visited_items: Set[Item] = set()

    def add_solution(solution: Solution) -> None:
        ingredient = solution.current_item
        if has_recipe(ingredient):
            log.debug('Partial solution found. Adding to solutions queue.')
            solutions.append(solution)
        else:
            log.debug('Not a craftable item.')

    while len(solutions) > 0:
        solution = solutions.pop(0)
        log.debug('Finding ingredients for %s...', solution.current_item)
        ingredients = get_ingredients(solution.current_item)
        log.debug('Found ingredients: %s', ', '.join([str(ing) for ing in ingredients]))
        for ingredient in ingredients:
            try:
                log.debug('Testing ingredient %s', ingredient)
                if isinstance(ingredient, Item):
                    if ingredient in visited_items:
                        log.debug('Item already considered before. Skipping...')
                        continue
                    log.debug('Ingredient identified as Item.')
                    visited_items.add(ingredient)
                    new_solution = solution.add_step(ingredient, StepType.Synthesize)
                    if ingredient is added_item:
                        log.debug('Complete solution found!')
                        return new_solution
                    else:
                        add_solution(new_solution)
                elif isinstance(ingredient, Category):
                    log.debug('Ingredient identified as Category.')
                    category_items = get_category_items(ingredient)
                    log.debug('Category %s has %i items', ingredient, len(category_items))
                    for cat_item in category_items:
                        log.debug('Testing item %s as %s ingredient', cat_item, ingredient)
                        if cat_item in visited_items:
                            log.debug('Item already considered before. Skipping...')
                            continue
                        visited_items.add(cat_item)
                        new_solution = solution.add_step(cat_item, StepType.SynthAsCat, ingredient)
                        if cat_item is added_item:
                            log.debug('Complete solution found!')
                            return new_solution
                        else:
                            add_solution(new_solution)
            except ValueError:
                continue
        if get_disassembly_sources is not None:
            log.debug('Checking Disassembly options...')
            disassemblies = get_disassembly_sources(solution.current_item)
            log.debug('Found %i disassemblies', len(disassemblies))
            for disassembly in disassemblies:
                try:
                    if disassembly in visited_items:
                        log.debug('Item already considered before. Skipping...')
                        continue
                    visited_items.add(disassembly)
                    new_solution = solution.add_step(disassembly, StepType.Synthesize)
                    if disassembly is added_item:
                        return new_solution
                    else:
                        add_solution(new_solution)
                except ValueError:
                    continue

    return None