from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from board import Board
    from player import Player


class Tile:
    """Base class for all board tiles."""

    def __init__(
        self,
        board: Board,
        position: int,
        name: str,
        tile_type: str,
        description: str ='',
    ):
        self._board = board
        self._position = position
        self._name = name
        self._tile_type = tile_type
        self._description = description

    def land_on(self, player: 'Player') -> None:
        """Handle what happens when a player lands on this tile."""
        print(f"[{player.piece}] {player.name} landed on {self.name} (Type: {self.type}).")
        if self.description():
            print(f"    -> {self.description}")
    

    def type(self) -> str:
        return self._tile_type

    def name(self) -> str:
        return self._name

    def description(self) -> str:
        return self._description

    def position(self) -> int:
        return self._position

    def board(self) -> Board:
        return self._board


class Property(Tile):

    def __init__(
        self,
        board: Board,
        position: int,
        name: str,
        tile_type: str,
        price: int,
        rent: int,
        mortgage: int,
        description: str,
    ):
        super().__init__(board, position, name, tile_type, description)
        self._price = price
        self._rent = rent
        self._mortgage = mortgage


class Street(Property):
    def __init__(
        self,
        board: Board,
        position: int,
        name: str,
        tile_type: str,
        color: str,
        price: int,
        rent: int,
        rent_with_color_set: int,
        rent_with_1_house: int,
        rent_with_2_houses: int,
        rent_with_3_houses: int,
        rent_with_4_houses: int,
        rent_with_hotel: int,
        house_cost: int,
        hotel_cost: int,
        mortgage: int,
        description: str,
    ):
        super().__init__(
            board, position, name, tile_type, price, rent, mortgage, description
        )
        self._color = color
        self._rent_with_color_set = rent_with_color_set
        self._rent_with_1_house = rent_with_1_house
        self._rent_with_2_houses = rent_with_2_houses
        self._rent_with_3_houses = rent_with_3_houses
        self._rent_with_4_houses = rent_with_4_houses
        self._rent_with_hotel = rent_with_hotel
        self._house_cost = house_cost
        self._hotel_cost = hotel_cost


# more subclasses
...


def build_tile(board: Board, data: dict[str, Any]) -> Tile:
    """Factory function to build Tile objects from JSON data."""
    # We extract the data using a .get so that if the data is missing a key it won't crash
    tile_type = data.get("type", "unknown")
    position = data.get("position", -1)
    name = data.get("name", "Unknown")
    description = data.get("description", "")

    if tile_type == "property":
        return Street(
            board=board,
            position=position,
            name=name,
            tile_type=tile_type,
            color=data.get("color", ""),
            price=data.get("price", 0),
            rent=data.get("rent", 0),
            rent_with_color_set=data.get("rentWithColorSet", 0),
            rent_with_1_house=data.get("rentWith1House", 0),
            rent_with_2_houses=data.get("rentWith2Houses", 0),
            rent_with_3_houses=data.get("rentWith3Houses", 0),
            rent_with_4_houses=data.get("rentWith4Houses", 0),
            rent_with_hotel=data.get("rentWithHotel", 0),
            house_cost=data.get("houseCost", 0),
            hotel_cost=data.get("hotelCost", 0),
            mortgage=data.get("mortgage", 0),
            description=description
        )
    
    # Fallback for special, tax, station, utility, chance, community_chest
    # We will add specific subclasses for these in the next steps.
    return Tile(board, position, name, tile_type, description)
