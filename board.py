"""
Core game engine and state orchestrator for the Monopoly simulation.

This module defines the `Board` class, which initializes the game environment
from JSON data, manages the main event loop, handles turn progression,
evaluates win/loss conditions, and coordinates visual frame generation.
"""

import random
import json
from player import Player, build_player
import pickle
import const as c
from player import Player
from tile import Tile, build_tile
from deck import Deck
from draw import draw


class Board:

    _chance_deck: Deck
    _community_chest_deck: Deck
    _tiles: list[Tile]
    _players: list[Player]
    _current_player_index: int
    _current_dice: tuple[int, int]
    _last_event: str
    _frame_counter: int

    def __init__(
        self,
        tiles_json_path: str,
        chance_json_path: str,
        community_chest_json_path: str,
        players_json_path: str,
        num_players: int,
    ):
        """
        Initialize the game board and load all required assets.

        Args:
            tiles_json_path (str): File path to the board layout JSON.
            chance_json_path (str): File path to the Chance deck JSON.
            community_chest_json_path (str): File path to the Community Chest deck JSON.
            players_json_path (str): File path to the player configuration JSON.
            num_players (int): The number of active players (typically 2 to 4).
        """
        self._tiles_json_path = tiles_json_path
        self._chance_json_path = chance_json_path
        self._community_chest_json_path = community_chest_json_path
        self._players_json_path = players_json_path
        self._num_players = num_players

        # Information gathered from the json
        self._chance_deck = Deck(chance_json_path, self)
        self._community_chest_deck = Deck(community_chest_json_path, self)
        self._tiles = self._load_tiles()
        self._players = self._load_players()

        # State tracking
        self._current_player_index = 0
        self._current_dice = (1, 1)
        self._last_event = "Game Started!"
        self._frame_counter = 0

    # Private methods

    def _load_tiles(self) -> list["Tile"]:
        """Reads the tiles.json file and builds the board."""
        with open(self._tiles_json_path, "r", encoding="utf-8") as file:
            tiles_data = json.load(file)

        board_tiles: list["Tile"] = []

        for tile_dict in tiles_data:
            new_tile = build_tile(self, tile_dict)
            board_tiles.append(new_tile)

        return board_tiles

    def _load_players(self) -> list["Player"]:
        """Reads the players.json file and builds the players."""
        with open(self._players_json_path, "r", encoding="utf-8") as file:
            players_data = json.load(file)

        players_data = players_data[: self._num_players]
        board_players: list["Player"] = []

        for index, player_dict in enumerate(players_data):
            new_player = build_player(self, player_dict, index)
            board_players.append(new_player)

        return board_players

    # Properties (Read-only access)

    @property
    def last_event(self) -> str:
        return self._last_event

    @property
    def chance_deck(self) -> Deck:
        return self._chance_deck

    @property
    def community_chest_deck(self) -> Deck:
        return self._community_chest_deck

    @property
    def tiles(self) -> list[Tile]:
        """Return the populated list of tiles"""
        return self._tiles

    @property
    def players(self) -> list[Player]:
        return self._players

    @property
    def dice(self) -> tuple[int, int]:
        return self._current_dice

    @property
    def current_player(self) -> Player:
        return self._players[self._current_player_index]

    @property
    def num_tiles(self) -> int:
        return len(self._tiles)

    @property
    def jail_position(self) -> int:
        return 10

    @property
    def is_double(self) -> bool:
        """Returns True if the last rolled dice have the same value."""
        return self._current_dice[0] == self._current_dice[1]

    @property
    def frame_counter(self) -> int:
        return self._frame_counter

    # Methods (Modification)

    def set_last_event(self, message: str) -> None:
        """Sets last event to print out."""
        self._last_event = message

    def add_one_frame_counter(self) -> None:
        """Adds one to the frame counter."""
        self._frame_counter += 1

    def take_snapshot(self, message: str) -> None:
        """Sets an event, takes a picture of the current board state and increments the counter."""
        self.set_last_event(message)
        draw(self, f"frames/frame_{self._frame_counter:04d}.svg")
        self.add_one_frame_counter()

    # Game-mechanics methods

    def play(self) -> None:
        """
        Execute the main game loop.

        Continuously iterates through player turns until an end condition is met
        (either the maximum turn limit is reached or only one player remains).
        Handles turn execution, bankruptcy checks, and portfolio management.
        """
        print("--- Starting Monopoly Simulation ---")
        self.take_snapshot("Game Started!")
        turn_count = 0

        # Main event loop: Runs until the turn limit is hit or a monopoly is achieved

        while not self._is_game_over(turn_count):
            player = self.current_player

            if player.is_bankrupt:
                self._advance_turn()
                continue

            self._execute_player_turn(player)

            # Post-turn resolution: Check for bankruptcy forced by external payments
            # (e.g., rent/taxes) before allowing the AI to invest remaining funds.
            if player.money < 0 and not player.is_bankrupt:
                player.declare_bankruptcy(self)
            else:
                player.strategy.manage_portfolio(player)

            self._advance_turn()
            turn_count += 1

        self._declare_winner(turn_count)

        print("--- Ended Monopoly Simulation ---")

    def _is_game_over(self, turn_count: int) -> bool:
        """Checks if the game has reached an end condition."""
        active_players = sum(1 for player in self._players if not player.is_bankrupt)
        return turn_count >= c.MAX_TURNS or active_players <= 1

    def _declare_winner(self, turn_count: int) -> None:
        """Prints the final results and renders the final frames."""
        self.take_snapshot(f"🏆 SIMULATION OVER after {turn_count} turns! 🏆")

        active_players = [p for p in self._players if not p.is_bankrupt]
        if active_players:
            winner = max(active_players, key=lambda p: p.money)
            self.take_snapshot(f"👑 Winner: {winner.name} with ${winner.money}!")

    def _execute_player_turn(self, player: Player) -> None:
        """Manages a player's turn, including potential multiple rolls for doubles."""
        active_turn = True
        doubles_count = 0

        self.take_snapshot(f"{player.piece} {player.name}'s turn")

        while active_turn:
            if player.is_in_jail:
                gets_normal_turn = self._handle_jail_logic(player)

                if not gets_normal_turn:
                    break

            # Normal roll logic
            active_turn, doubles_count = self._handle_normal_roll(player, doubles_count)

    def roll_dice(self) -> tuple[int, int]:
        """Rolls two random 6-sided dice and updates the board's current dice state."""
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        self._current_dice = (d1, d2)
        return self._current_dice

    def _advance_turn(self) -> None:
        """Moves the index to the next player."""
        self._current_player_index = (self._current_player_index + 1) % len(
            self._players
        )

    def _handle_normal_roll(
        self, player: "Player", doubles_count: int
    ) -> tuple[bool, int]:
        """
        Execute a standard dice roll, calculate movement, and enforce the speeding rule.

        Args:
            player (Player): The active player taking their turn.
            doubles_count (int): The number of consecutive doubles rolled this turn.

        Returns:
            tuple[bool, int]: A boolean indicating if the player gets to roll again
                (True) or if their turn ends (False), alongside the updated doubles count.
        """
        d1, d2 = self.roll_dice()
        total_roll = d1 + d2

        if self.is_double:
            doubles_count += 1
            # The "Speeding" rule: 3 consecutive doubles instantly sends the player to jail
            if doubles_count == 3:
                self.take_snapshot(f"🚨 {player.name} sped! 3 doubles = Jail!")
                player.go_to_jail()
                return False, doubles_count

            self.take_snapshot(f"🎲 {player.name} rolled {total_roll} (DOUBLE!)")
            player.move(total_roll)
            if player.is_in_jail:
                return False, doubles_count

            if player.money < 0:
                return False, doubles_count

            return True, doubles_count  # Roll again

        self.take_snapshot(f"🎲 {player.name} rolled {total_roll}.")
        player.move(total_roll)
        return False, doubles_count

    def _handle_jail_logic(self, player: Player) -> bool:
        """
        Execute jail escape attempts or penalty enforcement for an incarcerated player.

        Evaluates the use of 'Get Out of Jail Free' cards, rolling for doubles,
        or serving the mandatory sentence.

        Args:
            player (Player): The player currently in jail.

        Returns:
            bool: True if the player escapes cleanly and is permitted to take
                a normal movement roll immediately, False otherwise.
        """
        self.take_snapshot(
            f"🔒 {player.name} is in JAIL (Turns left: {player.turns_in_prison})"
        )

        if player.use_get_out_of_jail_card():
            self.take_snapshot(
                f"🎫 {player.name} used a Get Out of Jail Free card and is free!"
            )
            return True

        # Roll for escape
        d1, d2 = self.roll_dice()
        total_roll = d1 + d2

        if self.is_double:
            self.take_snapshot(
                f"🎲 {player.name} rolled doubles ({total_roll}) & escaped!"
            )
            player.release_from_jail()
            player.move(total_roll)

        else:
            player.decrement_jail_turn()
            if player.turns_in_prison == 0:
                self.take_snapshot(
                    f"💸 {player.name} has served its time and moved {total_roll}."
                )
                player.release_from_jail()
                player.move(total_roll)
            else:
                self.take_snapshot(
                    f"🔒 {player.name} rolled {total_roll}. Stuck in Jail."
                )

        return False


def save_board(board: Board, pickle_path: str) -> None:
    with open(pickle_path, "wb") as f:
        pickle.dump(board, f)


def load_board(pickle_path: str) -> Board:
    with open(pickle_path, "rb") as f:
        return pickle.load(f)
