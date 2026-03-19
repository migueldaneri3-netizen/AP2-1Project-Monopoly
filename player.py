from __future__ import annotations
from typing import TYPE_CHECKING, Any
from tile import Property
from strategy import PlayerStrategy, SimpleStrategy, SmartStrategy
import const as c
from draw import draw

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
    _turns_left_in_prison: int
    _owned_properties: list[Property]
    _strategy: PlayerStrategy
    _last_event: str
    _is_bankrupt_status: bool

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
        self._money = c.START_MONEY
        self._get_out_of_jail_free_cards = 0
        self._turns_left_in_prison = 0
        self._owned_properties = []
        self._strategy = SimpleStrategy()
        self._last_event = ""
        self._is_bankrupt_status = False

    # Properties (Read-only access)

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_bankrupt(self) -> bool:
        """A player is bankrupt if they have negative money."""
        return self._is_bankrupt_status

    @property
    def board(self) -> Board:
        return self._board

    @property
    def piece(self) -> str:
        return self._piece

    @property
    def color(self) -> str:
        return self._color

    @property
    def index(self) -> int:
        return self._index

    @property
    def money(self) -> int:
        return self._money

    @property
    def position(self) -> int:
        return self._position

    @property
    def get_out_of_jail_free_cards(self) -> int:
        return self._get_out_of_jail_free_cards

    @property
    def turns_in_prison(self) -> int:
        return self._turns_left_in_prison

    @property
    def owned_properties(self) -> list[Property]:
        return self._owned_properties

    @property
    def strategy(self) -> PlayerStrategy:
        return self._strategy

    @property
    def is_in_jail(self) -> bool:
        """Returns True if the player is currently serving time."""
        return self._turns_left_in_prison > 0

    # Methods (Modification)

    def set_strategy(self, strategy: PlayerStrategy) -> None:
        """Sets the player strategy"""
        self._strategy = strategy

    def set_last_event(self, message: str) -> None:
        """Sets the last event to be printed"""
        self._last_event = message

    def take_snapshot(self) -> None:
        """Takes a picture of the current board state and increments the counter."""
        draw(self._board, f"frames/frame_{self._board.frame_counter:04d}.svg")
        self.board.add_one_frame_counter()

    # In-game methods

    def move(self, spaces: int) -> None:
        """Moves the player forward by a given number of spaces."""
        old_position = self._position
        total_tiles = self._board.num_tiles

        # Calculate new position using modulo to wrap around the board
        self._position = (old_position + spaces) % total_tiles

        # If the new position is smaller than the old one, we passed or landed on GO
        if self._position < old_position:
            self._money += c.GO_SALARY
            self.set_last_event(
                f"🎉 {self._name} passed GO and collected ${c.GO_SALARY}!"
            )
            self.take_snapshot()

        # Trigger the land-on logic for the new tile
        target_tile = self._board.tiles[self._position]
        target_tile.land_on(self)

    def set_position(self, new_position: int) -> None:
        """Updates the player's position without passing go."""
        self._position = new_position

    def add_get_out_of_jail_free_card(self) -> None:
        """Grants the player a Get Out of Jail Free card."""
        self._get_out_of_jail_free_cards += 1

    def add_property(self, property_tile: "Property") -> None:
        """Adds a property to the player's portfolio."""
        self._owned_properties.append(property_tile)

    def pay(self, amount: int) -> None:
        """Subtracts money from the player."""
        self._money -= amount

    def receive(self, amount: int) -> None:
        """Adds money to the player."""
        self._money += amount

    def declare_bankruptcy(self, board: "Board") -> None:
        """Handles the bankruptcy process: resets money and returns properties to the bank."""
        board.take_snapshot(f"💀 {self.name} went bankrupt!")

        self._is_bankrupt_status = True
        self._money = 0
        self._get_out_of_jail_free_cards = 0

        for prop in self._owned_properties:
            prop.reset_ownership()

        self._owned_properties.clear()

        self._turns_left_in_prison = 0

    # Jail logic

    def go_to_jail(self) -> None:
        """Sends the player directly to jail without passing GO."""
        self._position = self._board.jail_position

        self._turns_left_in_prison = 3

        self.set_last_event(
            f"🚨 {self._name} was caught speeding! Go directly to Jail. Do not pass GO."
        )
        self.take_snapshot()

    def use_get_out_of_jail_card(self) -> bool:
        """Attempts to use a card. Returns True if successful."""
        if self._get_out_of_jail_free_cards > 0:
            self._get_out_of_jail_free_cards -= 1
            self.release_from_jail()
            return True
        return False

    def decrement_jail_turn(self) -> None:
        """Reduces the remaining jail time by 1."""
        self._turns_left_in_prison -= 1

    def release_from_jail(self) -> None:
        """Clears the jail status."""
        self._turns_left_in_prison = 0


def build_player(board: Board, data: dict[str, Any], index: int) -> Player:

    player = Player(board, data["name"], data["piece"], data["color"], index)

    # The first player recieves the smart strategy, all other players keep the basic one
    if index < c.SMART_PLAYERS:
        player.set_strategy(SmartStrategy())

    return player
