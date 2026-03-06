from __future__ import annotations
from typing import TYPE_CHECKING
import tile  # Importing your own file is Pylance-approved and uses 0 external libraries!

if TYPE_CHECKING:
    from player import Player


class PlayerStrategy:
    """Pas 5.1: Interfície d'estratègia per decisions del jugador."""

    def should_buy_property(
        self, player: "Player", property_tile: "tile.Property"
    ) -> bool:
        raise NotImplementedError("Subclasses must implement should_buy_property")

    def manage_portfolio(self, player: "Player") -> None:
        """Allows the strategy to build houses/hotels or sell them."""
        pass


class SimpleStrategy(PlayerStrategy):
    """Pas 5.2: Estratègia simple (comprar sempre, no construir)."""

    def should_buy_property(
        self, player: "Player", property_tile: "tile.Property"
    ) -> bool:
        return player.money() >= getattr(property_tile, "_price", 0)

    def manage_portfolio(self, player: "Player") -> None:
        # The simple bot never builds!
        pass


class SmartStrategy(PlayerStrategy):
    """Pas 5.3 & 6: Estratègia millorada amb gestió intel·ligent i construcció."""

    def should_buy_property(
        self, player: "Player", property_tile: "tile.Property"
    ) -> bool:
        price = getattr(property_tile, "_price", 0)

        if player.money() < price:
            return False
        if property_tile.type() == "station":
            return True
        if player.money() - price >= 300:
            return True

        if property_tile.type() == "property":
            target_color = getattr(property_tile, "_color", None)
            owns_same_color = any(
                getattr(p, "_color", None) == target_color
                for p in player.owned_properties()
                if p.type() == "property"
            )
            if owns_same_color:
                return True

        return False

    def manage_portfolio(self, player: "Player") -> None:
        """Evaluates owned properties to build, sell, mortgage, or unmortgage."""
        owned_props = player.owned_properties()

        # 1. SURVIVAL MODE: If we are broke or below our £300 emergency fund, raise cash!
        if player.money() < 300:
            for prop in owned_props:
                # Sell houses first
                if isinstance(prop, tile.Street):
                    while prop.can_sell_house() and player.money() < 300:
                        prop.sell_house()
                    if prop.can_sell_hotel() and player.money() < 300:
                        prop.sell_hotel()

                # If still poor, start mortgaging properties
                if prop.can_mortgage() and player.money() < 300:
                    prop.mortgage()

        # 2. PROSPERITY MODE: If we have excess cash, unmortgage things before building
        elif player.money() > 500:
            for prop in owned_props:
                if getattr(prop, "_is_mortgaged", False) and prop.can_unmortgage():
                    # Keep a buffer so we don't unmortgage ourselves into poverty
                    cost = int(getattr(prop, "_mortgage", 0) * 1.1)
                    if player.money() - cost >= 300:
                        prop.unmortgage()

        # 3. BUILD MODE: Build houses/hotels if funds permit (Same as before)
        for prop in owned_props:
            if isinstance(prop, tile.Street):
                if prop.can_build_hotel():
                    if (player.money() - getattr(prop, "_hotel_cost", 0)) >= 300:
                        prop.build_hotel()

                while prop.can_build_house():
                    if (player.money() - getattr(prop, "_house_cost", 0)) < 300:
                        break
                    prop.build_house()
