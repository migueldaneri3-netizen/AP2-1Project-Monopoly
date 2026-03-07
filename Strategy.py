from __future__ import annotations
from typing import TYPE_CHECKING
import tile

# Avoids import error
if TYPE_CHECKING:
    from player import Player


class PlayerStrategy:
    """Abstract base class for the interface of all strategies.
    This class acts as a formal contract to ensure that different strategies implementations
    are interchangeable without modifying the core game engine."""

    def should_buy_property(
        self, player: "Player", property_tile: "tile.Property"
    ) -> bool:
        """
        Determine whether the player should purchase a landed-on property.

        Args:
            player: The player instance making the decision.
            property_tile: The specific property tile available for purchase.

        Returns:
            bool: True if the property should be bought, False otherwise.

        Raises:
            NotImplementedError: This method must be overridden by concrete strategies.
        """

        raise NotImplementedError("Subclasses must implement should_buy_property")

    def manage_portfolio(self, player: "Player") -> None:
        """
        Perform mid-turn actions such as building or selling houses.

        Args:
            player: The player instance managing their portfolio.
        """

        # Default implementation: Do nothing.
        pass


class SimpleStrategy(PlayerStrategy):
    """Simple strategy. Player buys properties as long as he can. Player never buys nor sells houses."""

    def should_buy_property(
        self, player: "Player", property_tile: "tile.Property"
    ) -> bool:
        """Returns True if the player has enough money to buy the property."""
        return player.money() >= property_tile.price()

    def manage_portfolio(self, player: "Player") -> None:
        """Does nothing: this strategy does not develop properties."""
        pass


class SmartStrategy(PlayerStrategy):
    """Smart strategy with buildings and management of assets and liquidity."""

    LIQUIDITY_SAFE_NET = 300
    INVESTMENT_TRESHOLD = 500

    def should_buy_property(
        self, player: "Player", property_tile: "tile.Property"
    ) -> bool:
        """Evaluates property purchases based on liquidity.

        Rules for buying:
        1. Always rejects if funds are insufficient.
        2. Always buys 'station' and same-color-tiles regardless of the cash buffer.
        3. Buys other properties only if it leaves a $300 safety net.
        """

        price = property_tile.price()

        if player.money() < price:
            return False

        if property_tile.type() == "station":
            return True

        # Aim for same-color streets
        if property_tile.type() == "street":
            target_color = property_tile.color()

            if target_color:
                if any(
                    prop.color() == target_color for prop in player.owned_properties()
                ):
                    return True

        # Ensure liquidity at all times
        if player.money() - price >= self.LIQUIDITY_SAFE_NET:
            return True

        return False

    def manage_portfolio(self, player: "Player") -> None:
        """Manages post-movement actions of the player following 3 scenarios:
        1. Raising cash if it's below $300
        2. Unmortgage if cash is high
        3. Build houses & hotels if founds permit it."""

        # 1. Raise cash
        if player.money() < self.LIQUIDITY_SAFE_NET:
            for prop in player.owned_properties():
                if player.money() >= self.LIQUIDITY_SAFE_NET:
                    break  # Stop liquidating.

                if isinstance(prop, tile.Street):
                    if prop.can_sell_hotel():
                        prop.sell_hotel()

                    while (
                        prop.can_sell_house()
                        and player.money() < self.LIQUIDITY_SAFE_NET
                    ):
                        prop.sell_house()

                if prop.can_mortgage() and player.money() < self.LIQUIDITY_SAFE_NET:
                    prop.mortgage()

        # 2. Unmortgage
        elif player.money() > self.INVESTMENT_TRESHOLD:
            for prop in player.owned_properties():
                if prop.is_mortgaged() and prop.can_unmortgage():
                    if (
                        player.money() - prop.unmortgage_price()
                        >= self.LIQUIDITY_SAFE_NET
                    ):
                        prop.unmortgage()

        # 3. Build improvements
        if player.money() > self.LIQUIDITY_SAFE_NET:
            for prop in player.owned_properties():
                if isinstance(prop, tile.Street):
                    if (
                        prop.can_build_hotel()
                        and (player.money() - prop.hotel_cost())
                        >= self.LIQUIDITY_SAFE_NET
                    ):
                        prop.build_hotel()

                    while prop.can_build_house():
                        if (
                            player.money() - prop.house_cost()
                        ) < self.LIQUIDITY_SAFE_NET:
                            break
                        prop.build_house()
