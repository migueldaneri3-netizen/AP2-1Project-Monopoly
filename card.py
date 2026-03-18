from __future__ import annotations
from typing import TYPE_CHECKING, Any
import tile

if TYPE_CHECKING:
    from player import Player
    from board import Board


class Card:
    """Base class for all cards"""

    _id: int
    _title: str
    _description: str
    _action: str
    _keep_card: bool

    def __init__(self, data: dict[str, Any]):
        self._id: int = data["id"]
        self._title: str = data.get("title", "")
        self._description: str = data.get("description", "")
        self._action: str = data.get("action", "")
        self._keep_card: bool = data.get("keepCard", False)

    def execute(self, player: "Player", board: "Board") -> None:
        """
        Coordinates the card's execution process.

        Updates the board state with the card's description and triggers the specific logic
        defined in the subclass.

        Arguments:
            player: The player who drew the card.
            board: The current game board.
        """
        board.take_snapshot(f"🃏 {player.name} drew: {self._description}")
        self._do_execute(player, board)

    def _do_execute(self, player: "Player", board: "Board") -> None:
        """Implementation of the specific card action.

        This method must be overridden by subclasses to define what actually happens to the player.

        Arguments:
            player: The player to be affected by the action.
            board: The board to be modified by the action.

        Raises:
            NotImplementedError: If the subclass does not override this method."""
        raise NotImplementedError("Subclasses must implement _do_execute")

    @property
    def keep_card(self) -> bool:
        return self._keep_card


class MoneyCard(Card):
    """A card that modifies a player's balance."""

    _amount: int

    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
        self._amount: int = data.get("amount", 0)

    def _do_execute(self, player: "Player", board: "Board") -> None:
        """Executes the financial transfer (pay or receive)."""
        if self._action == "collect_money":
            player.receive(self._amount)
        elif self._action == "pay_money":
            player.pay(self._amount)


class MoveCard(Card):
    """A card that modifies a player's position"""

    _position: int
    _spaces: int

    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
        self._position: int = data.get("position", -1)
        self._spaces: int = data.get("spaces", 0)

    def _do_execute(self, player: "Player", board: "Board") -> None:
        """Executes the movement"""
        old_pos = player.position

        if self._action == "move_to_position":
            if self._position < old_pos and self._position != board.jail_position:
                player.receive(200)
                board.take_snapshot(f"💰 {player.name} passed GO and collected £200!")

            player.set_position(self._position)

        elif self._action == "move_back_spaces":
            player.set_position((old_pos - self._spaces) % board.num_tiles)

        elif self._action in ("move_to_nearest_station", "move_to_nearest_utility"):

            if "station" in self._action:
                target_type = "station"
            else:
                target_type = "utility"

            for i in range(1, board.num_tiles + 1):
                check_pos = (old_pos + i) % board.num_tiles
                if board.tiles[check_pos].type == target_type:
                    if check_pos < old_pos:
                        player.receive(200)
                    player.set_position(check_pos)
                    break

        board.tiles[player.position].land_on(player)


class JailCard(Card):
    """A card which sends you to jail or which can be used to get out of jail when needed."""

    def _do_execute(self, player: "Player", board: "Board") -> None:
        """Executes the corresponding action."""
        if self._action == "go_to_jail":
            player.go_to_jail()
        elif self._action == "get_out_of_jail_card":
            player.add_get_out_of_jail_free_card()


class PlayerInteractionCard(Card):
    """A card which makes the player pay or recieve money to/from other players."""

    _amount: int

    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
        self._amount: int = data.get("amountPerPlayer", 0)

    def _do_execute(self, player: "Player", board: "Board") -> None:
        """Executes the correspondin monetary transaction."""

        if self._action == "pay_each_player":
            for other_player in board.players:
                if other_player != player:
                    player.pay(self._amount)
                    other_player.receive(self._amount)

        elif self._action == "collect_from_players":
            for other_player in board.players:
                if other_player != player:
                    other_player.pay(self._amount)
                    player.receive(self._amount)


class PropertyAssessmentCard(Card):
    """A card which makes the player pay for each hotel or house owned."""

    _per_house: int
    _per_hotel: int

    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
        self.per_house: int = data.get("amountPerHouse", 0)
        self.per_hotel: int = data.get("amountPerHotel", 0)

    def _do_execute(self, player: "Player", board: "Board") -> None:
        """Executes the payment for property owned."""
        total = 0
        for prop in player.owned_properties:
            if isinstance(prop, tile.Street):
                total += (prop.houses * self.per_house) + (prop.hotels * self.per_hotel)
        if total > 0:
            player.pay(total)
            board.take_snapshot(f"🛠️ {player.name} paid ${total} for property repairs.")


def build_card(data: dict[str, Any]) -> Card:
    """Factory to map JSON actions to the correct Card class."""
    action = data.get("action", "")
    if "money" in action:
        return MoneyCard(data)
    if "move" in action:
        return MoveCard(data)
    if "jail" in action:
        return JailCard(data)
    if "player" in action:
        return PlayerInteractionCard(data)
    if "property" in action:
        return PropertyAssessmentCard(data)
    return Card(data)  # Fallback
