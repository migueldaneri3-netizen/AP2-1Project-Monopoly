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
    ):
        self._tiles_json_path = tiles_json_path
        self._chance_json_path = chance_json_path
        self._community_chest_json_path = community_chest_json_path
        self._players_json_path = players_json_path

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

        board_players: list["Player"] = []

        for index, player_dict in enumerate(players_data):
            # Using the factory function from player.py
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

    def roll_dice(self) -> tuple[int, int]:
        """Rolls two random 6-sided dice and updates the board's current dice state."""
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        self._current_dice = (d1, d2)
        return self._current_dice

    def take_snapshot(self, message: str) -> None:
        """Sets an event, takes a picture of the current board state and increments the counter."""
        self.set_last_event(message)
        draw(self, f"frames/frame_{self._frame_counter:04d}.svg")
        self.add_one_frame_counter()

    def play(self) -> None:
        """Main game loop orchestrator."""
        print("--- Starting Monopoly Simulation ---")
        self.take_snapshot("Game Started!")
        turn_count = 0

        while not self._is_game_over(turn_count):
            player = self.current_player

            if player.is_bankrupt:
                self._advance_turn()
                continue

            self._execute_player_turn(player)

            if player.money < 0 and not player.is_bankrupt:
                player.declare_bankruptcy(self)
            else:
                player.strategy.manage_portfolio(player)

            self._advance_turn()
            turn_count += 1

        self._declare_winner(turn_count)
        print("--- Ended Monopoly Simulation ---")

    def _declare_winner(self, turn_count: int) -> None:
        """Prints the final results and renders the final frames."""
        self.take_snapshot(f"🏆 SIMULATION OVER after {turn_count} turns! 🏆")

        active_players = [p for p in self._players if not p.is_bankrupt]
        if active_players:
            winner = max(active_players, key=lambda p: p.money)
            self.take_snapshot(f"👑 Winner: {winner.name} with ${winner.money}!")

    def _is_game_over(self, turn_count: int) -> bool:
        """Checks if the game has reached an end condition."""
        active_players = sum(1 for player in self._players if not player.is_bankrupt)
        return turn_count >= c.MAX_TURNS or active_players <= 1

    def _advance_turn(self) -> None:
        """Moves the index to the next player."""
        self._current_player_index = (self._current_player_index + 1) % len(
            self._players
        )

    def _handle_jail_logic(self, player: Player) -> bool:
        """Executes jail rules.
        Returns True if the player escapes cleanly and takes a normal turn."""
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
                    f"💸 {player.name} did a Rita-Hayworth and moved {total_roll}."
                )
                player.release_from_jail()
                player.move(total_roll)
            else:
                self.take_snapshot(
                    f"🔒 {player.name} rolled {total_roll}. Stuck in Jail."
                )

        return False

    def _handle_normal_roll(
        self, player: "Player", doubles_count: int
    ) -> tuple[bool, int]:
        """
        Executes a standard dice roll and movement.
        Returns a tuple: (is_turn_still_active, updated_doubles_count).
        """
        d1, d2 = self.roll_dice()
        total_roll = d1 + d2

        if self.is_double:
            doubles_count += 1
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


def save_board(board: Board, pickle_path: str) -> None:
    with open(pickle_path, "wb") as f:
        pickle.dump(board, f)


def load_board(pickle_path: str) -> Board:
    with open(pickle_path, "rb") as f:
        return pickle.load(f)
