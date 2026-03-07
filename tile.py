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
    
    def is_mortgaged(self) -> bool:
        return self._is_mortgaged
    
    def is_owned(self) -> bool:
        return self._owner is not None

    def calculate_rent(self, dice_roll: int) -> int:
        """Base rent calculation. Overridden by subclasses."""
        return self._base_rent

    def price(self) -> int:
        return self._price
    
    def unmortgage_price(self) -> int:
        return int(self._mortgage * 1.1)

    # --- PAS 7: Hipoteques (Base Property) ---

    def can_mortgage(self) -> bool:
        """Pas 7.1: A property can be mortgaged if it's owned and not already mortgaged."""
        if self.owner() is None or self._is_mortgaged:
            return False
        return True

    def mortgage(self) -> None:
        """Pas 7.1: Mortgage the property and receive the mortgage value."""
        current_owner = self.owner()
        if current_owner is not None and self.can_mortgage():
            self._is_mortgaged = True
            current_owner.receive(self._mortgage)
            print(
                f"    -> 🏦 {current_owner.name()} mortgaged {self.name()} for £{self._mortgage}."
            )

    def can_unmortgage(self) -> bool:
        """Pas 7.2: Can unmortgage if owned, mortgaged, and the player has enough money (mortgage + 10%)."""
        current_owner = self.owner()
        if current_owner is None or not self._is_mortgaged:
            return False
        
        return current_owner.money() >= self.unmortgage_price()

    def unmortgage(self) -> None:
        """Pas 7.2: Pay the mortgage value + 10% interest to unmortgage."""
        current_owner = self.owner()
        if current_owner is not None and self.can_unmortgage():
            cost = int(self._mortgage * 1.1)
            current_owner.pay(cost)
            self._is_mortgaged = False
            print(
                f"    -> 💸 {current_owner.name()} unmortgaged {self.name()} for £{cost}."
            )

    def color(self) -> str | None:
        return None
    
    def buy(self, player: "Player") -> None:
        player.pay(self._price)
        self._owner = player
        player.add_property(self)
        # 🛠️ Add this:
        self._board.set_last_event(f"💰 {player.name()} bought {self.name()}!")

    def land_on(self, player: "Player") -> None:
        """Step 4.5 & 5: Buy if free (based on strategy), pay rent if occupied."""
        # Using Tile's base land_on for the standard log
        super(Property, self).land_on(player)

        current_owner = self.owner()

        if current_owner is None:
            # Ask the strategy!
            if player.strategy().should_buy_property(player, self):
                # Double check they actually have the funds, just to be safe against bad strategy logic
                if player.money() >= self._price:
                    self.buy(player)
            else:
                print(f"    -> 🛑 {player.name()} decided NOT to buy {self.name()}.")

        elif current_owner != player and not self._is_mortgaged:
            # Rent payment logic remains exactly the same as Step 4
            dice_roll = sum(self._board.dice())
            rent_amt = self.calculate_rent(dice_roll)

            print(f"    -> Owned by {current_owner.name()}. Rent is £{rent_amt}.")
            player.pay(rent_amt)
            current_owner.receive(rent_amt)
            print(
                f"    -> 💸 {player.name()} paid £{rent_amt} to {current_owner.name()}."
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

    def color(self) -> str:
        return self._color
    
    def calculate_rent(self, dice_roll: int) -> int:
        """Step 4.2: Calculate rent based on development and monopoly."""
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

        # Double rent if the color set is owned but undeveloped
        if self.has_monopoly():
            return self._rent_with_color_set

        return self._base_rent

    def can_mortgage(self) -> bool:
        """Pas 7.1 Constraint: Cannot mortgage a street with buildings."""
        if self.houses > 0 or self.hotels > 0:
            return False
        # If it has no buildings, fall back to the base Property rules
        return super().can_mortgage()

    def _get_color_group(self) -> list["Street"]:
        """Helper to get all streets of the same color."""
        # Using isinstance tells Pylance exactly what type we are filtering for
        return [
            t
            for t in self._board.tiles()
            if isinstance(t, Street) and getattr(t, "_color", "") == self._color
        ]

    def has_monopoly(self) -> bool:
        """Verifies if the owner owns all streets of this color."""
        current_owner = self.owner()
        if current_owner is None:
            return False

        group = self._get_color_group()
        return all(street.owner() == current_owner for street in group)

    # --- PAS 6.1: Compra de cases ---

    def can_build_house(self) -> bool:
        """Checks monopoly, funds, and uniform building rules."""
        current_owner = self.owner()
        if current_owner is None:
            return False

        if not self.has_monopoly():
            return False
        if self.hotels > 0 or self.houses == 4:
            return False

        if current_owner.money() < self._house_cost:
            return False

        group = self._get_color_group()
        # Uniform rule: No other street in the group can have fewer houses than this one.
        for street in group:
            if street.hotels == 0 and street.houses < self.houses:
                return False
        return True

    def build_house(self) -> None:
        current_owner = self.owner()
        if current_owner is not None and self.can_build_house():
            current_owner.pay(self._house_cost)
            self.houses += 1
            print(
                f"    -> 🏠 {current_owner.name()} built house #{self.houses} on {self.name()} for £{self._house_cost}!"
            )

    # --- PAS 6.2: Compra d'hotels ---

    def can_build_hotel(self) -> bool:
        """Checks if 4 houses are built uniformly and funds are available."""
        current_owner = self.owner()
        if current_owner is None:
            return False

        if not self.has_monopoly():
            return False
        if self.houses != 4 or self.hotels > 0:
            return False

        if current_owner.money() < self._hotel_cost:
            return False

        group = self._get_color_group()
        # Uniform rule: All other streets must also have 4 houses or a hotel
        for street in group:
            if street.hotels == 0 and street.houses < 4:
                return False
        return True
    
    def hotel_cost(self) -> int:
        return self._hotel_cost

    def house_cost(self) -> int:
        return self._house_cost

    def build_hotel(self) -> None:
        current_owner = self.owner()
        if current_owner is not None and self.can_build_hotel():
            current_owner.pay(self._hotel_cost)
            self.houses = 0  # 4 houses are returned to the bank
            self.hotels = 1
            print(
                f"    -> 🏢 {current_owner.name()} upgraded to a HOTEL on {self.name()} for £{self._hotel_cost}!"
            )

    # --- PAS 6.3: Venda (Mantenint uniformitat i meitat de preu) ---

    def can_sell_house(self) -> bool:
        if self.owner() is None:
            return False
        if self.houses == 0:
            return False

        group = self._get_color_group()
        # Uniform rule: Cannot sell if another street has MORE houses than this one
        for street in group:
            if street.hotels > 0 or street.houses > self.houses:
                return False
        return True

    def sell_house(self) -> None:
        current_owner = self.owner()
        if current_owner is not None and self.can_sell_house():
            recoup_amount = self._house_cost // 2  # Bank pays half
            current_owner.receive(recoup_amount)
            self.houses -= 1
            print(
                f"    -> 🔨 {current_owner.name()} sold a house on {self.name()} for £{recoup_amount}."
            )

    def can_sell_hotel(self) -> bool:
        if self.owner() is None:
            return False
        return self.hotels == 1

    def sell_hotel(self) -> None:
        current_owner = self.owner()
        if current_owner is not None and self.can_sell_hotel():
            recoup_amount = self._hotel_cost // 2
            current_owner.receive(recoup_amount)
            self.hotels = 0
            self.houses = 4  # Degrades back to 4 houses
            print(
                f"    -> 🔨 {current_owner.name()} sold a hotel on {self.name()} for £{recoup_amount}."
            )


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


class CardSquare(Tile):
    """Pas 8.4: Caselles de targetes (ChanceSquare, CommunityChestSquare)"""

    def __init__(
        self, board: "Board", position: int, name: str, tile_type: str, description: str
    ):
        super().__init__(board, position, name, tile_type, description)

    def land_on(self, player: "Player") -> None:
        super().land_on(player)

        # Determine which deck to pull from
        if self.type() == "chance":
            card = self._board.chance_deck().draw()
        else:
            card = self._board.community_chest_deck().draw()

        card.execute(player, self._board)


class GoToJailSquare(Tile):
    """Pas 9.1: Casella que envia directament a la presó."""

    def land_on(self, player: "Player") -> None:
        super().land_on(player)
        player.go_to_jail()


class TaxSquare(Tile):
    """Casella d'impostos que dedueix diners directament."""

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
        super().land_on(player)
        player.pay(self._amount)
        # 🛠️ Add this:
        self._board.set_last_event(f"🏛️ {player.name()} paid £{self._amount} in taxes!")


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
        # Check for 'amount' first, fallback to 'price' or a default of 200
        tax_amount = data.get("amount", data.get("price", 200))
        return TaxSquare(board, position, name, tile_type, description, tax_amount)

    # Fallback for GO, Free Parking, etc.
    return Tile(board, position, name, tile_type, description)
