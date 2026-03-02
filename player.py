from __future__ import annotations
from typing import TYPE_CHECKING, Any
from tile import Property

if TYPE_CHECKING:
    from board import Board


class Player:
    _board: Board
    _name: str
    _piece: str
    _color: str
    _index: int
    _position: int
    _money: int
    _get_out_of_jail_free_cards: int
    _turns_in_prision: int
    _owned_properties: list[Property]

    def __init__(
        self,
        board: Board,
        name: str,
        piece: str,
        color: str,
        index: int,
    ):
        # Attributes passed from the JSON
        self._board = board
        self._name = name
        self._piece = piece
        self._color = color
        self._index = index

        # Game state attributes
        self._position = 0  # Everyone starts on GO
        self._money = 1500  # Starting money
        self._get_out_of_jail_free_cards = 0
        self._turns_in_prison = 0
        self._owned_properties = []

    def board(self) -> Board:
        return self._board

    def name(self) -> str:
        return self._name

    def piece(self) -> str:
        return self._piece

    def color(self) -> str:
        return self._color

    def index(self) -> int:
        return self._index

    def broke(self) -> bool:
        """Return True if the player has negative money."""
        return self._money < 0

    def money(self) -> int:
        return self._money

    def position(self) -> int:
        return self._position

    def get_out_of_jail_free_cards(self) -> int:
        return self._get_out_of_jail_free_cards

    def turns_in_prison(self) -> int:
        return self._turns_in_prison

    def owned_properties(self) -> list[Property]:
        return self._owned_properties

    def move(self, spaces: int) -> None:
        """Moves the player forward by a given number of spaces."""
        old_position = self._position
        total_tiles = self._board.num_tiles()

        # Calculate new position using modulo to wrap around the board
        self._position = (old_position + spaces) % total_tiles

        # If the new position is smaller than the old one, we passed or landed on GO
        if self._position < old_position:
            self._money += 200
            print(
                f"🎉 [{self.piece}] {self._name} passed GO and collected £200! New balance: £{self._money}"
            )

        # Trigger the land_on logic for the new tile
        target_tile = self._board.tiles()[self._position]
        target_tile.land_on(self)

    def go_to_jail(self) -> None:
        """Sends the player directly to jail without passing GO."""
        # Update position to the jail tile (index 10)
        self._position = self._board.jail_position()

        # We set this to 3 to indicate they are now locked up
        # (We will use this in a future step for jail turns)
        self._turns_in_prison = 3

        print(
            f"🚨 [{self.piece()}] {self._name} was caught speeding! Go directly to Jail. Do not pass GO."
        )


def build_player(board: Board, data: dict[str, Any], index: int) -> Player:
    """Build a Player from JSON-like dict with 'name', 'piece', and 'color' keys."""
    return Player(board, data["name"], data["piece"], data["color"], index)
