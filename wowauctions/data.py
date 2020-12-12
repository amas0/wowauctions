from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    id: int
    name: str
    item_class: str
    item_subclass: str
    quality: str


@dataclass(frozen=True)
class Auction:
    id: int
    item: Item
    quantity: int
    unit_price: int
    buyout: int
    time_left: str

    @property
    def time_left_key(self):
        mapping = {
            'VERY_LONG': 4,
            'LONG': 3,
            'MEDIUM': 2,
            'SHORT': 1
        }
        return mapping.get(self.time_left)
