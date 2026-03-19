"""
Player strategy implementations for automated decision-making.

This module uses the Strategy Design Pattern to define how players evaluate
property purchases, manage liquidity, and develop their real estate portfolios.
It includes an abstract base class and concrete implementations (Simple, Smart).
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import tile

if TYPE_CHECKING:
    from player import Player


class PlayerStrategy:
    """Abstract base class for the interface of all strategies."""

    def should_buy_property(
        self, player: "Player", property_tile: "tile.Property"
    ) -> bool:
        """
        Determine whether the player should purchase a landed-on property.

        Arguments:
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
        Perform mid-turn financial actions such as building, selling, or mortgaging.

        Arguments:
            player (Player): The player instance managing their portfolio.
        """

        # Default implementation: Do nothing.
        pass


class SimpleStrategy(PlayerStrategy):
    """Simple strategy. Player buys properties as long as he can. Player never buys nor sells houses."""

    def should_buy_property(
        self, player: "Player", property_tile: "tile.Property"
    ) -> bool:
        """
        Determine if the player should buy the property (always buys if affordable).

        Args:
            player (Player): The player attempting the purchase.
            property_tile (tile.Property): The property being evaluated.

        Returns:
            bool: True if the player has enough money, False otherwise.
        """
        return player.money >= property_tile.price

    def manage_portfolio(self, player: "Player") -> None:
        """
        Does nothing; the simple strategy does not manage or develop assets.

        Args:
            player (Player): The player instance.
        """
        pass


class SmartStrategy(PlayerStrategy):
    """Smart strategy with buildings and management of assets and liquidity."""

    LIQUIDITY_SAFE_NET = (
        300  # Minimum cash buffer to maintain for unexpected rents/taxes
    )
    INVESTMENT_TRESHOLD = (
        500  # Minimum cash required before considering property development
    )
    CRITICAL_TRESHOLD = 50  # Cash drop point that triggers emergency asset liquidation

    def should_buy_property(
        self, player: "Player", property_tile: "tile.Property"
    ) -> bool:
        """
        Evaluate a property purchase based on color sets and liquidity safety nets.

        Rules for buying:
        1. Always rejects if funds are insufficient.
        2. Always buys 'station' tiles and same-color-tiles regardless of the cash buffer.
        3. Buys other properties only if it leaves a $300 safety net.

        Args:
            player (Player): The player attempting the purchase.
            property_tile (tile.Property): The property being evaluated.

        Returns:
            bool: True if the purchase aligns with the strategic rules, False otherwise.
        """

        price = property_tile.price

        if player.money < price:
            return False

        if property_tile.type == "station":
            return True

        # Aim for same-color streets
        if property_tile.type == "street":
            target_color = property_tile.color

            if target_color:
                if any(prop.color == target_color for prop in player.owned_properties):
                    return True

        # Ensure liquidity at all times
        if player.money - price >= self.LIQUIDITY_SAFE_NET:
            return True

        return False

    def manage_portfolio(self, player: "Player") -> None:
        """
        Trigger specific financial management routines based on current liquidity thresholds.

        Args:
            player (Player): The player instance managing their portfolio.
        """

        # Scenario 1. Critical liquidity
        if player.money < self.CRITICAL_TRESHOLD:
            self._survival_mode(player)

        # Scenario 2. High Liquidity
        if player.money > self.LIQUIDITY_SAFE_NET:
            self._unmortgaging_mode(player)

        # Scenario 3. Asset Improvement
        if player.money > self.INVESTMENT_TRESHOLD:
            self._growth_mode(player)

    def _survival_mode(self, player: "Player") -> None:
        """
        Liquidate assets (sell buildings, mortgage properties) to restore the safety net.

        Args:
            player (Player): The player in critical financial condition.
        """
        # Iterate through properties and degrade them step-by-step (sell hotels -> sell houses -> mortgage)
        # until the player's cash reaches the liquidity safe net.
        for prop in player.owned_properties:
            if player.money >= self.LIQUIDITY_SAFE_NET:
                break  # Stop liquidating.

            if isinstance(prop, tile.Street):
                if prop.can_sell_hotel:
                    prop.sell_hotel()

                while prop.can_sell_house and player.money < self.LIQUIDITY_SAFE_NET:
                    prop.sell_house()

            if prop.can_mortgage and player.money < self.LIQUIDITY_SAFE_NET:
                prop.mortgage()

    def _unmortgaging_mode(self, player: "Player"):
        """
        Uses excess cash to unmortgage properties.

        Args:
            player (Player): The player instance.
        """

        for prop in player.owned_properties:
            if prop.is_mortgaged and prop.can_unmortgage:
                if player.money - prop.unmortgage_price >= self.LIQUIDITY_SAFE_NET:
                    prop.unmortgage()

    def _growth_mode(self, player: "Player"):
        """
        Invests in property improvements while respecting the safety net.

        Args:
            player (Player): The player instance.
        """

        if player.money > self.LIQUIDITY_SAFE_NET:
            # Scan properties for development opportunities. Prioritizes upgrading to hotels if
            # conditions are met, otherwise builds houses incrementally as long as funds allow.
            for prop in player.owned_properties:
                if isinstance(prop, tile.Street):
                    if (
                        prop.can_build_hotel
                        and (player.money - prop.hotel_cost) >= self.LIQUIDITY_SAFE_NET
                    ):
                        prop.build_hotel()

                    while prop.can_build_house:
                        if (player.money - prop.house_cost) < self.LIQUIDITY_SAFE_NET:
                            break
                        prop.build_house()
