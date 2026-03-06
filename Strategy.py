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
        """Pas 10: Executa accions post-moviment d'una en una segons l'estat financer."""

        # --- PHASE 1: SURVIVAL (Raise cash if below £300) ---
        if player.money() < 300:
            for prop in player.owned_properties():
                if player.money() >= 300:
                    break  # Survived! Stop liquidating.

                if isinstance(prop, tile.Street):
                    # Sell hotels one by one
                    if prop.can_sell_hotel():
                        prop.sell_hotel()

                    # Sell houses one by one
                    while prop.can_sell_house() and player.money() < 300:
                        prop.sell_house()

                # Mortgage one by one
                if prop.can_mortgage() and player.money() < 300:
                    prop.mortgage()

        # --- PHASE 2: PROSPERITY (Unmortgage if cash is high) ---
        elif player.money() > 500:
            for prop in player.owned_properties():
                if getattr(prop, "_is_mortgaged", False) and prop.can_unmortgage():
                    cost = int(getattr(prop, "_mortgage", 0) * 1.1)
                    if player.money() - cost >= 300:
                        prop.unmortgage()

        # --- PHASE 3: GROWTH (Build houses/hotels if funds permit) ---
        if player.money() > 300:
            for prop in player.owned_properties():
                if isinstance(prop, tile.Street):

                    # Upgrade to hotel
                    if (
                        prop.can_build_hotel()
                        and (player.money() - getattr(prop, "_hotel_cost", 0)) >= 300
                    ):
                        prop.build_hotel()

                    # Build houses one by one
                    while prop.can_build_house():
                        if (player.money() - getattr(prop, "_house_cost", 0)) < 300:
                            break
                        prop.build_house()
