import csv
import logging
from os import path
from typing import Dict, Iterable, List, Tuple

from atelier_types import Category, Disassembly, Item, ItemType, Recipe

item_cats:      Dict[str, Tuple[str, List[Item]]] = dict()
all_cats:       Dict[str, Category] = dict()
all_items:      Dict[str, Item] = dict()
all_recipes:    Dict[str, Recipe] = dict()
all_desynths:   Dict[str, Disassembly] = dict()

def _check_init():
    if len(all_items) <= 0:
        raise Exception('Data not yet loaded.')

def get_item(item_name: str) -> Item:
    _check_init()
    for item in all_items.values():
        if item_name == item.internal_name or item_name == item.display_name:
            return item
    raise KeyError(f'Could not find item "{item_name}"')

def get_ingredients(item: Item) -> List[Category | Item]:
    _check_init()
    return all_recipes[item.internal_name].ingredients

def get_category_items(category: Category, synthesis_only: bool = False) -> List[Item]:
    _check_init()
    _, items = item_cats[category.internal_name]
    if synthesis_only:
        items = [item for item in items if item.internal_name in all_recipes.keys()]
    return items

def get_disassemblies(target_item: Item) -> List[Disassembly]:
    _check_init()
    return [diss for diss in all_desynths.values() if target_item in diss.props_inherited_by]

def get_disassembly_sources(target_item: Item) -> List[Item]:
    _check_init()
    return [disassembly.source_item for disassembly in get_disassemblies(target_item)]

def has_recipe(item: Item) -> bool:
    _check_init()
    return item.internal_name in all_recipes.keys()

def load_data(log: logging.Logger, force: bool = False) -> None:
    if len(all_items) > 0 and not force:
        raise Exception('Data already loaded.')

    data_path = path.join(path.dirname(__file__), 'data')

    def read_rows(filename: str):
        with open(path.join(data_path,filename), encoding='utf8') as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader, None)
            yield from csv_reader

    log.info('Clearing all data...')
    item_cats.clear()
    all_cats.clear()
    all_items.clear()
    all_recipes.clear()
    all_desynths.clear()

    for row in read_rows('Categories.csv'):
        category: Category = Category(row[0], row[1])
        log.debug('Category loaded: %s (%s)', category.display_name, category.internal_name)
        all_cats[category.internal_name] = category
        item_cats[category.internal_name] = (category.display_name, list())
    log.info('Categories loaded: %i', len(all_cats))

    for row in read_rows('Items.csv'):
        categories = [x for x in row[13].split(',') if x]
        item: Item = Item(row[1], row[24], ItemType(row[3]), categories)
        log.debug('Item loaded: %s (%s)', item.display_name, item.internal_name)
        log.debug('Item categories: %s', ', '.join(categories))

        for cat in categories:
            (_, items) = item_cats[cat]
            items.append(item)

        all_items[item.internal_name] = item
    log.info('Items loaded: %i', len(all_items))

    for row in read_rows('ItemData.csv'):
        if row[0] in all_items:
            item = all_items[row[0]]
            item.is_stackable = row[4] == '1'

    for row in read_rows('Ingredients.csv'):
        recipe_name = row[0]
        recipe_item = all_items[recipe_name]
        log.debug('Reading ingredients for %s', recipe_item.display_name)
        ingredient_list: List[Category | Item] = list()
        for ingredient in range(4):
            ingredient_name = row[1+(ingredient * 3)]
            if ingredient_name == '':
                break
            ingredient_is_cat = (row[2+(ingredient * 3)] == '1')
            if ingredient_is_cat:
                ingredient_category = all_cats[ingredient_name]
                log.debug('Read %s as category ingredient', ingredient_category.display_name)
                ingredient_list.append(ingredient_category)
            else:
                ingredient_item = all_items[ingredient_name]
                log.debug('Read %s as item ingredient', ingredient_item.display_name)
                ingredient_list.append(ingredient_item)
        recipe = Recipe(recipe_item, ingredient_list)
        all_recipes[row[0]] = recipe
    log.info('Recipes loaded: %i', len(all_recipes))

    for row in read_rows('Disassembly.csv'):
        disassembled_item = get_item(row[0])
        log.debug('Reading disassembly for %s', disassembled_item.display_name)
        results: List[Item] = [get_item(row[1])]
        if row[2]:
            results.append(get_item(row[2]))
        log.debug('Item disassembles into %s', ', '.join([item.display_name for item in results]))
        non_stack_results: List[Item]
        if disassembled_item.is_stackable:
            non_stack_results = list()
            log.debug('No properties to inherit.')
        else:
            non_stack_results = [item for item in results if not item.is_stackable]
            log.debug('Properties inherited by %s', ', '.join([item.display_name for item in non_stack_results]))
        disassembly = Disassembly(disassembled_item, results, non_stack_results)
        all_desynths[disassembled_item.internal_name] = disassembly
    log.info('Disassemblies loaded: %i', len(all_desynths))

    log.info('Loaded all information.')

def get_item_names(items: Iterable[Item]) -> List[str]:
    _check_init()
    return [name for item in items for name in (item.display_name, item.internal_name)]

def get_trait_donors() -> List[Item]:
    _check_init()
    return [item for item in all_items.values() if not item.is_stackable]

def get_trait_recipients() -> List[Item]:
    _check_init()
    return [all_items[recipe_name] for recipe_name in all_recipes]