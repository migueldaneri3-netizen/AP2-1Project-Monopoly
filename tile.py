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
        description: str = "",
    ):
        self._board = board
        self._position = position
        self._name = name
        self._tile_type = tile_type
        self._description = description

    def land_on(self, player: "Player") -> None:
        """Handle what happens when a player lands on this tile."""
        print(
            f"🏎️​  [{player.piece()}] {player.name()} landed on {self.name()} (Type: {self.type()})."
        )
        if self.description():
            print(f"    -> {self.description()}")

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
        board: "Board",
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
        self._base_rent = rent
        self._mortgage = mortgage

        # State variables for Step 4.1
        self._owner: Player | None = None
        self._is_mortgaged: bool = False

    def owner(self) -> Player | None:
        return self._owner

    def is_owned(self) -> bool:
        return self._owner is not None

    def calculate_rent(self, dice_roll: int) -> int:
        """Base rent calculation. Overridden by subclasses."""
        return self._base_rent

    def buy(self, player: "Player") -> None:
        """Handles the transaction of buying the property."""
        player.pay(self._price)
        self._owner = player
        player.add_property(self)
        print(f"    -> 💰 {player.name()} bought {self.name()} for £{self._price}!")

    def land_on(self, player: "Player") -> None:
        """Step 4.5: Buy if free, pay rent if owned."""
        super().land_on(player)

        if not self.is_owned():
            # Auto-buy logic for testing (if they have enough money)
            if player.money() >= self._price:
                self.buy(player)
            else:
                print(f"    -> Not enough money to buy {self.name()} (£{self._price}).")

        elif self.owner() != player and not self._is_mortgaged:
            # It's owned by someone else! Calculate and pay rent.
            dice_roll = sum(self._board.dice())
            rent_amt = self.calculate_rent(dice_roll)

            print(f"    -> Owned by {self.owner().name()}. Rent is £{rent_amt}.")
            player.pay(rent_amt)
            self.owner().receive(rent_amt)
            print(
                f"    -> 💸 {player.name()} paid £{rent_amt} to {self.owner().name()}."
            )


class Street(Property):
    def __init__(
        self,
        board: "Board",
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

        # Step 4.2 tracking
        self.houses: int = 0
        self.hotels: int = 0

    def calculate_rent(self, dice_roll: int) -> int:
        """Step 4.2: Calculate rent based on development."""
        if self.hotels > 0:
            return self._rent_with_hotel
        if self.houses == 4:
            return self._rent_with_4_houses
        if self.houses == 3:
            return self._rent_with_3_houses
        if self.houses == 2:
            return self._rent_with_2_houses
        if self.houses == 1:
            return self._rent_with_1_house
        # TODO in a later step: check if full color set is owned for 2x rent
        return self._base_rent


class Station(Property):
    def __init__(
        self,
        board: "Board",
        position: int,
        name: str,
        tile_type: str,
        price: int,
        rent: int,
        rent_with_2_stations: int,
        rent_with_3_stations: int,
        rent_with_4_stations: int,
        mortgage: int,
        description: str,
    ):
        super().__init__(
            board, position, name, tile_type, price, rent, mortgage, description
        )
        self._rent_with_2_stations = rent_with_2_stations
        self._rent_with_3_stations = rent_with_3_stations
        self._rent_with_4_stations = rent_with_4_stations

    def calculate_rent(self, dice_roll: int) -> int:
        """Step 4.3: Rent doubles for each station owned."""
        owner = self.owner()
        if not owner:
            return 0

        # Count how many stations the owner has
        stations_owned = sum(
            1 for p in owner.owned_properties() if p.type() == "station"
        )

        if stations_owned == 4:
            return self._rent_with_4_stations
        if stations_owned == 3:
            return self._rent_with_3_stations
        if stations_owned == 2:
            return self._rent_with_2_stations
        return self._base_rent


class Utility(Property):
    def __init__(
        self,
        board: "Board",
        position: int,
        name: str,
        tile_type: str,
        price: int,
        rent_multiplier: int,
        rent_multiplier_with_both: int,
        mortgage: int,
        description: str,
    ):
        # Base rent is 0 because it's purely multiplier based
        super().__init__(
            board, position, name, tile_type, price, 0, mortgage, description
        )
        self._rent_multiplier = rent_multiplier
        self._rent_multiplier_with_both = rent_multiplier_with_both

    def calculate_rent(self, dice_roll: int) -> int:
        """Step 4.4: Rent is dice roll * multiplier."""
        owner = self.owner()
        if not owner:
            return 0

        utils_owned = sum(1 for p in owner.owned_properties() if p.type() == "utility")
        multiplier = (
            self._rent_multiplier_with_both
            if utils_owned == 2
            else self._rent_multiplier
        )

        return dice_roll * multiplier


def build_tile(board: "Board", data: dict[str, Any]) -> Tile:
    tile_type = data.get("type", "unknown")
    position = data.get("position", -1)
    name = data.get("name", "Unknown")
    description = data.get("description", "")
    price = data.get("price", 0)
    mortgage = data.get("mortgage", 0)

    if tile_type == "property":
        return Street(
            board,
            position,
            name,
            tile_type,
            data.get("color", ""),
            price,
            data.get("rent", 0),
            data.get("rentWithColorSet", 0),
            data.get("rentWith1House", 0),
            data.get("rentWith2Houses", 0),
            data.get("rentWith3Houses", 0),
            data.get("rentWith4Houses", 0),
            data.get("rentWithHotel", 0),
            data.get("houseCost", 0),
            data.get("hotelCost", 0),
            mortgage,
            description,
        )

    elif tile_type == "station":
        return Station(
            board,
            position,
            name,
            tile_type,
            price,
            data.get("rent", 0),
            data.get("rentWith2Stations", 0),
            data.get("rentWith3Stations", 0),
            data.get("rentWith4Stations", 0),
            mortgage,
            description,
        )

    elif tile_type == "utility":
        return Utility(
            board,
            position,
            name,
            tile_type,
            price,
            data.get("rentMultiplier", 0),
            data.get("rentMultiplierWithBoth", 0),
            mortgage,
            description,
        )

    # Fallback for special, tax, chance, community_chest
    return Tile(board, position, name, tile_type, description)
