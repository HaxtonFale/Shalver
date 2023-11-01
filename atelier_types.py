from enum import StrEnum
from typing import List

class ItemType(StrEnum):
    Material    = 'Material'
    Usable      = 'Usable'
    Synthesis   = 'Synthesis'
    Equipment   = 'Equipment'

class Category:
    def __init__(self, internal_name: str, display_name: str) -> None:
        self.internal_name = internal_name
        self.display_name = display_name

    def __repr__(self):
        return self.display_name

class Item:
    def __init__(self, internal_name: str, display_name: str, item_type: ItemType, categories: List[str]) -> None:
        self.internal_name = internal_name
        self.display_name = display_name
        self.type = item_type
        self.categories = categories
        self.is_stackable: bool

    def __repr__(self):
        return self.display_name

class Recipe:
    def __init__(self, item: Item, ingredients: List[Category | Item]) -> None:
        self.item = item
        self.ingredients = ingredients

class Disassembly:
    def __init__(self, source_item: Item, results: List[Item], props_inherited_by: List[Item]) -> None:
        self.source_item = source_item
        self.results = results
        self.props_inherited_by = props_inherited_by