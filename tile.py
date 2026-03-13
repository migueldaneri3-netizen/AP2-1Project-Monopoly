from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from board import Board
    from player import Player


class Tile:
    """Base class for all board tiles."""

    _board: Board
    _position: int
    _name: str
    _tile_type: str
    _description: str

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

    # Properties

    @property
    def type(self) -> str:
        return self._tile_type

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def position(self) -> int:
        return self._position

    @property
    def board(self) -> Board:
        return self._board

    # Methods

    def land_on(self, player: "Player") -> None:
        """Handle what happens when a player lands on this tile."""
        self.board.take_snapshot(f"🏎️​ {player.name} landed on {self.name}")


class Property(Tile):
    """Represents a purchasable tile on the board that can generate rent."""

    _price: int
    _rent: int
    _mortgage: int
    _owner: Player | None
    _is_mortgaged: bool

    def __init__(
        self,
        board: "Board",
        position: int,
        name: str,
        tile_type: str,
        description: str,
        price: int,
        rent: int,
        mortgage: int,
    ):
        super().__init__(board, position, name, tile_type, description)
        self._price = price
        self._base_rent = rent
        self._mortgage = mortgage

        self._owner = None
        self._is_mortgaged = False

    # Properties

    @property
    def owner(self) -> Player | None:
        return self._owner

    @property
    def is_mortgaged(self) -> bool:
        return self._is_mortgaged

    @property
    def is_owned(self) -> bool:
        return self._owner is not None

    @property
    def price(self) -> int:
        return self._price

    @property
    def unmortgage_price(self) -> int:
        return int(self._mortgage * 1.1)

    @property
    def can_mortgage(self) -> bool:
        """A property can be mortgaged if it's owned and not already mortgaged."""
        if self.owner is None or self._is_mortgaged:
            return False
        return True

    @property
    def can_unmortgage(self) -> bool:
        """Can unmortgage if owned, mortgaged, and the player has enough money (mortgage + 10%)."""
        current_owner = self.owner
        if current_owner is None or not self._is_mortgaged:
            return False

        return current_owner.money >= self.unmortgage_price

    @property
    def color(self) -> str | None:
        return None

    # Methods

    def reset_ownership(self) -> None:
        """Returns the property to the bank and clears any mortgages."""
        self._owner = None
        self._is_mortgaged = False

    def calculate_rent(self, dice_roll: int) -> int:
        """Base rent calculation. Overridden by subclasses."""
        return self._base_rent

    def mortgage(self) -> None:
        """Mortgage the property and receive the mortgage value."""
        current_owner = self.owner

        if current_owner is not None and self.can_mortgage:
            self._is_mortgaged = True
            current_owner.receive(self._mortgage)
            self.board.take_snapshot(
                f"🏦 {current_owner.name} mortgaged {self.name} for ${self._mortgage}."
            )

    def unmortgage(self) -> None:
        """Pay the mortgage value + 10% interest to unmortgage."""
        current_owner = self.owner

        if current_owner is not None and self.can_unmortgage:
            cost = self.unmortgage_price
            current_owner.pay(cost)
            self._is_mortgaged = False
            self.board.take_snapshot(
                f" 💸 {current_owner.name} unmortgaged {self.name} for ${cost}."
            )

    def buy(self, player: "Player") -> None:
        """Buy the property paying the cost to the bank"""
        player.pay(self._price)
        self._owner = player
        player.add_property(self)
        self._board.take_snapshot(
            f"💰 {player.name} bought {self.name} for ${self._price}!"
        )

    def land_on(self, player: "Player") -> None:
        """Buy if free, pay rent if occupied."""
        super(Property, self).land_on(player)

        current_owner = self.owner

        if current_owner is None:
            if player.strategy.should_buy_property(player, self):
                if player.money >= self._price:
                    self.buy(player)
            else:
                self.board.take_snapshot(
                    f"🛑 {player.name} decided NOT to buy {self.name}."
                )

        elif current_owner != player and not self._is_mortgaged:

            dice_roll = sum(self._board.dice)
            rent_amt = self.calculate_rent(dice_roll)

            self.board.take_snapshot(
                f"Owned by {current_owner.name}. Rent is ${rent_amt}."
            )
            player.pay(rent_amt)
            current_owner.receive(rent_amt)
            self.board.take_snapshot(
                f"💸 {player.name} paid ${rent_amt} to {current_owner.name}."
            )


class Street(Property):
    """Represents a street property with color"""

    _color: str
    _rent_with_color_set: int
    _rent_with_1_house: int
    _rent_with_2_houses: int
    _rent_with_3_houses: int
    _rent_with_4_houses: int
    _rent_with_hotel: int
    _house_cost: int
    _hotel_cost: int
    _houses: int
    _hotels: int

    def __init__(
        self,
        board: "Board",
        position: int,
        name: str,
        tile_type: str,
        description: str,
        price: int,
        rent: int,
        mortgage: int,
        color: str,
        rent_with_color_set: int,
        rent_with_1_house: int,
        rent_with_2_houses: int,
        rent_with_3_houses: int,
        rent_with_4_houses: int,
        rent_with_hotel: int,
        house_cost: int,
        hotel_cost: int,
    ):
        super().__init__(
            board, position, name, tile_type, description, price, rent, mortgage
        )
        self._owner = None
        self._color = color
        self._rent_with_color_set = rent_with_color_set
        self._rent_with_1_house = rent_with_1_house
        self._rent_with_2_houses = rent_with_2_houses
        self._rent_with_3_houses = rent_with_3_houses
        self._rent_with_4_houses = rent_with_4_houses
        self._rent_with_hotel = rent_with_hotel
        self._house_cost = house_cost
        self._hotel_cost = hotel_cost

        self._houses = 0
        self._hotels = 0

    @property
    def can_mortgage(self) -> bool:
        """Cannot mortgage a street with buildings."""
        if self._houses > 0 or self._hotels > 0:
            return False
        return super().can_mortgage

    @property
    def has_monopoly(self) -> bool:
        """Verifies if the owner owns all streets of this color."""
        current_owner = self.owner
        if current_owner is None:
            return False

        group = self._get_color_group()
        return all(street.owner == current_owner for street in group)

    @property
    def can_build_house(self) -> bool:
        """Checks monopoly, funds, and uniform building rules."""
        current_owner = self.owner
        if current_owner is None:
            return False

        if not self.has_monopoly:
            return False

        if self._hotels > 0 or self._houses == 4:
            return False

        if current_owner.money < self._house_cost:
            return False

        group = self._get_color_group()

        # Uniform rule: No other street in the group can have fewer houses than this one.
        for street in group:
            if street._hotels == 0 and street._houses < self._houses:
                return False
        return True

    @property
    def houses(self) -> int:
        return self._houses

    @property
    def hotels(self) -> int:
        return self._hotels

    @property
    def color(self) -> str:
        return self._color

    @property
    def can_build_hotel(self) -> bool:
        """Checks if 4 houses are built uniformly and funds are available."""
        current_owner = self.owner
        if current_owner is None:
            return False

        if not self.has_monopoly:
            return False

        if self._houses != 4 or self._hotels > 0:
            return False

        if current_owner.money < self._hotel_cost:
            return False

        group = self._get_color_group()

        # Uniform rule: All other streets must also have 4 houses or a hotel
        for street in group:
            if street._hotels == 0 and street._houses < 4:
                return False
        return True

    @property
    def hotel_cost(self) -> int:
        return self._hotel_cost

    @property
    def house_cost(self) -> int:
        return self._house_cost

    @property
    def can_sell_house(self) -> bool:
        if self.owner is None:
            return False
        if self._houses == 0:
            return False

        group = self._get_color_group()

        # Uniform rule: Cannot sell if another street has MORE houses than this one
        for street in group:
            if street._hotels > 0 or street._houses > self._houses:
                return False
        return True

    @property
    def can_sell_hotel(self) -> bool:
        if self.owner is None:
            return False
        return self._hotels == 1

    def reset_ownership(self) -> None:
        """Returns the street to the bank and destructs all buildings."""
        super().reset_ownership()
        self._houses = 0
        self._hotels = 0

    def calculate_rent(self, dice_roll: int) -> int:
        """Calculate rent based on development and monopoly."""
        if self._hotels > 0:
            return self._rent_with_hotel
        if self._houses == 4:
            return self._rent_with_4_houses
        if self._houses == 3:
            return self._rent_with_3_houses
        if self._houses == 2:
            return self._rent_with_2_houses
        if self._houses == 1:
            return self._rent_with_1_house

        # Double rent if the color set is owned but undeveloped
        if self.has_monopoly:
            return self._rent_with_color_set

        return self._base_rent

    def _get_color_group(self) -> list["Street"]:
        """Helper to get all streets of the same color."""
        return [
            t
            for t in self._board.tiles
            if isinstance(t, Street) and getattr(t, "_color", "") == self._color
        ]

    def build_house(self) -> None:
        """Builds a house on the selected property"""
        current_owner = self.owner
        if current_owner is not None and self.can_build_house:
            current_owner.pay(self._house_cost)
            self._houses += 1
            self.board.take_snapshot(
                f"🏠 {current_owner.name} built house #{self._houses} on {self.name} for ${self._house_cost}!"
            )

    def build_hotel(self) -> None:
        """Builds a hotel on the selected property"""
        current_owner = self.owner
        if current_owner is not None and self.can_build_hotel:
            current_owner.pay(self._hotel_cost)
            self._houses = 0
            self._hotels = 1
            self.board.take_snapshot(
                f" 🏢 {current_owner.name} upgraded to a HOTEL on {self.name} for ${self._hotel_cost}!"
            )

    def sell_house(self) -> None:
        """Sells a house from this street."""
        current_owner = self.owner
        if current_owner is not None and self.can_sell_house:
            recoup_amount = self._house_cost // 2  # Bank pays half
            current_owner.receive(recoup_amount)
            self._houses -= 1
            self.board.take_snapshot(
                f"🔨 {current_owner.name} sold a house on {self.name} for ${recoup_amount}."
            )

    def sell_hotel(self) -> None:
        """Sells a hotels from the selected street."""
        current_owner = self.owner
        if current_owner is not None and self.can_sell_hotel:
            recoup_amount = self._hotel_cost // 2
            current_owner.receive(recoup_amount)
            self._hotels = 0
            self._houses = 4  # Degrades back to 4 houses
            self.board.take_snapshot(
                f"🔨 {current_owner.name} sold a hotel on {self.name} for ${recoup_amount}."
            )


class Station(Property):
    """Represents station properties."""

    _rent_with_2_stations: int
    _rent_with_3_stations: int
    _rent_with_4_stations: int

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
            board, position, name, tile_type, description, price, rent, mortgage
        )
        self._rent_with_2_stations = rent_with_2_stations
        self._rent_with_3_stations = rent_with_3_stations
        self._rent_with_4_stations = rent_with_4_stations

    def calculate_rent(self, dice_roll: int) -> int:
        """Rent doubles for each station owned."""
        owner = self.owner

        if not owner:
            return 0

        stations_owned = sum(
            1 for prop in owner.owned_properties if prop.type == "station"
        )

        if stations_owned == 4:
            return self._rent_with_4_stations
        if stations_owned == 3:
            return self._rent_with_3_stations
        if stations_owned == 2:
            return self._rent_with_2_stations
        return self._base_rent


class Utility(Property):
    """Represent utilities properties."""

    _rent_multiplier: int
    _rent_multiplier_with_both: int

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
            board,
            position,
            name,
            tile_type,
            description,
            price,
            0,
            mortgage,
        )

        self._rent_multiplier = rent_multiplier
        self._rent_multiplier_with_both = rent_multiplier_with_both

    def calculate_rent(self, dice_roll: int) -> int:
        """Rent is dice roll * multiplier."""
        owner = self.owner

        if not owner:
            return 0

        utils_owned = sum(
            1 for prop in owner.owned_properties if prop.type == "utility"
        )
        if utils_owned == 1:
            multiplier = self._rent_multiplier
        else:
            multiplier = self._rent_multiplier_with_both

        return dice_roll * multiplier


class CardSquare(Tile):
    """Represents cards tiles (ChanceSquare, CommunityChestSquare)."""

    def __init__(
        self, board: "Board", position: int, name: str, tile_type: str, description: str
    ):
        super().__init__(board, position, name, tile_type, description)

    def land_on(self, player: "Player") -> None:
        """Manages what happens when a player lands on this tile."""
        super().land_on(player)

        if self.type == "chance":
            card = self._board.chance_deck.draw()
        else:
            card = self._board.community_chest_deck.draw()

        card.execute(player, self._board)


class GoToJailSquare(Tile):
    """Tile which directly sends to jail."""

    def land_on(self, player: "Player") -> None:
        """Sends to prision."""
        super().land_on(player)
        player.go_to_jail()


class TaxSquare(Tile):
    """Taxes tiles which substract money."""

    _amount: int

    def __init__(
        self,
        board: "Board",
        position: int,
        name: str,
        tile_type: str,
        description: str,
        amount: int,
    ):
        super().__init__(board, position, name, tile_type, description)
        self._amount = amount

    def land_on(self, player: "Player") -> None:
        """Deducts money from player."""
        super().land_on(player)
        player.pay(self._amount)
        self._board.take_snapshot(f"🏛️ {player.name} paid ${self._amount} in taxes!")


def build_tile(board: "Board", data: dict[str, Any]) -> Tile:
    """Builds tile from the json data."""
    tile_type = data.get("type", "unknown")
    position = data.get("position", -1)
    name = data.get("name", "Unknown")
    description = data.get("description", "")
    price = data.get("price", 0)
    mortgage = data.get("mortgage", 0)

    if tile_type == "property":
        return Street(
            board=board,
            position=position,
            name=name,
            tile_type=tile_type,
            description=description,
            price=price,
            rent=data.get("rent", 0),
            mortgage=mortgage,
            color=data.get("color", ""),
            rent_with_color_set=data.get("rentWithColorSet", 0),
            rent_with_1_house=data.get("rentWith1House", 0),
            rent_with_2_houses=data.get("rentWith2Houses", 0),
            rent_with_3_houses=data.get("rentWith3Houses", 0),
            rent_with_4_houses=data.get("rentWith4Houses", 0),
            rent_with_hotel=data.get("rentWithHotel", 0),
            house_cost=data.get("houseCost", 0),
            hotel_cost=data.get("hotelCost", 0),
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

    elif tile_type in ("chance", "community_chest"):
        return CardSquare(board, position, name, tile_type, description)

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

    elif tile_type == "special":
        if name == "Go To Jail":
            return GoToJailSquare(board, position, name, tile_type, description)

    elif tile_type == "tax":
        tax_amount = data.get("amount", data.get("price", 200))
        return TaxSquare(board, position, name, tile_type, description, tax_amount)

    # Fallback for GO, Free Parking, etc.
    return Tile(board, position, name, tile_type, description)
