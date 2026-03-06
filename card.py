from __future__ import annotations
from typing import TYPE_CHECKING, Any
import tile

if TYPE_CHECKING:
    from player import Player
    from board import Board


class Card:
    """Pas 8.1: Implementar la classe Card base."""

    def __init__(self, data: dict[str, Any]):
        self.id: int = data["id"]
        self.title: str = data.get("title", "")
        self.description: str = data.get("description", "")
        self.action: str = data.get("action", "")
        self.keep_card: bool = data.get("keepCard", False)

    def execute(self, player: "Player", board: "Board") -> None:
        print(f"    -> 🃏 {player.name()} drew: {self.description}")
        self._do_execute(player, board)

    def _do_execute(self, player: "Player", board: "Board") -> None:
        raise NotImplementedError("Subclasses must implement _do_execute")


# --- Pas 8.3: Subclasses for different card types ---


class MoneyCard(Card):
    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
        self.amount: int = data.get("amount", 0)

    def _do_execute(self, player: "Player", board: "Board") -> None:
        if self.action == "collect_money":
            player.receive(self.amount)
        elif self.action == "pay_money":
            player.pay(self.amount)


class MoveCard(Card):
    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
        self.position: int = data.get("position", -1)
        self.spaces: int = data.get("spaces", 0)

    def _do_execute(self, player: "Player", board: "Board") -> None:
        old_pos = player.position()

        if self.action == "move_to_position":
            if self.position < old_pos and self.position != board.jail_position():
                player.receive(200)
                print(f"    -> 💰 {player.name()} passed GO and collected £200!")

            # FIXED: Use the setter method
            player.set_position(self.position)

        elif self.action == "move_back_spaces":
            # FIXED: Use the setter method
            player.set_position((old_pos - self.spaces) % board.num_tiles())

        elif self.action in ("move_to_nearest_station", "move_to_nearest_utility"):
            target_type = "station" if "station" in self.action else "utility"
            for i in range(1, board.num_tiles() + 1):
                check_pos = (old_pos + i) % board.num_tiles()
                if board.tiles()[check_pos].type() == target_type:
                    if check_pos < old_pos:
                        player.receive(200)

                    # FIXED: Use the setter method
                    player.set_position(check_pos)
                    break

        # Land on the new tile
        board.tiles()[player.position()].land_on(player)


class JailCard(Card):
    def _do_execute(self, player: 'Player', board: 'Board') -> None:
        if self.action == "go_to_jail":
            player.go_to_jail()
        elif self.action == "get_out_of_jail_card":
            # FIXED: Use the setter method
            player.add_get_out_of_jail_free_card()


class PlayerInteractionCard(Card):
    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
        self.amount: int = data.get("amountPerPlayer", 0)

    def _do_execute(self, player: "Player", board: "Board") -> None:
        if self.action == "pay_each_player":
            for other in board.players():
                if other != player:
                    player.pay(self.amount)
                    other.receive(self.amount)
        elif self.action == "collect_from_players":
            for other in board.players():
                if other != player:
                    other.pay(self.amount)
                    player.receive(self.amount)


class PropertyAssessmentCard(Card):
    def __init__(self, data: dict[str, Any]):
        super().__init__(data)
        self.per_house: int = data.get("amountPerHouse", 0)
        self.per_hotel: int = data.get("amountPerHotel", 0)

    def _do_execute(self, player: "Player", board: "Board") -> None:
        total = 0
        for prop in player.owned_properties():
            if isinstance(prop, tile.Street):
                total += (prop.houses * self.per_house) + (prop.hotels * self.per_hotel)
        if total > 0:
            player.pay(total)
            print(f"    -> 🛠️ {player.name()} paid £{total} for property repairs.")


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
