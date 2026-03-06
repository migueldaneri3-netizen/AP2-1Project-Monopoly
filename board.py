import random
import json
from player import Player, build_player
import pickle
from player import Player
from tile import Tile, build_tile
from draw import draw


class Board:
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

        # Load the tiles immediately upon creating the board
        self._tiles: list["Tile"] = self._load_tiles()
        self._players: list["Player"] = self._load_players()

        # State tracking
        self._current_player_index: int = 0
        self._current_dice: tuple[int, int] = (1, 1)

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
        with open(self._players_json_path, "r", encoding="utf-8") as file:
            players_data = json.load(file)

        board_players: list["Player"] = []
        for index, player_dict in enumerate(players_data):
            # Using the factory function from player.py
            new_player = build_player(self, player_dict, index)
            board_players.append(new_player)

        return board_players

    def tiles(self) -> list[Tile]:
        """Return the populated list of tiles"""
        return self._tiles

    def players(self) -> list[Player]:
        return self._players

    def dice(self) -> tuple[int, int]:
        return self._current_dice

    def current_player(self) -> Player:
        return self._players[self._current_player_index]

    def num_tiles(self) -> int:
        return len(self._tiles)

    def jail_position(self) -> int:
        return 10

    def roll_dice(self) -> tuple[int, int]:
        """Rolls two 6-sided dice and updates the board's current dice state."""
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        self._current_dice = (d1, d2)
        return self._current_dice

    def is_double(self) -> bool:
        """Returns True if the last rolled dice have the same value."""
        return self._current_dice[0] == self._current_dice[1]

    def play(self) -> None:
        """Game loop that generates SVG frames for the web viewer."""
        print("--- Starting Monopoly Simulation ---")
        frame_counter = 0

        # 1. Take snapshot of the initial starting board
        draw(self, f"frame_{frame_counter:04d}.svg")
        frame_counter += 1

        for _ in range(8):
            player = self.current_player()
            active_turn = True
            doubles_count = 0

            print(f"\n--- [{player.piece()}] {player.name()}'s turn ---")

            while active_turn:
                d1, d2 = self.roll_dice()
                total_roll = d1 + d2
                roll_msg = f"🎲 [{player.piece()}] {player.name()} rolls {d1} and {d2} (Total: {total_roll})"

                if self.is_double():
                    doubles_count += 1
                    roll_msg += " 🎲 DOUBLE!"
                    print(roll_msg)

                    if doubles_count == 3:
                        player.go_to_jail()
                        active_turn = False
                    else:
                        player.move(total_roll)
                        print(" 🔄 Rolls again!")
                else:
                    print(roll_msg)
                    player.move(total_roll)
                    active_turn = False

                # 2. Take a snapshot after the player completes their movement
                draw(self, f"frame_{frame_counter:04d}.svg")
                frame_counter += 1

            # Move to next player
            self._current_player_index = (self._current_player_index + 1) % len(
                self._players
            )

        print(f"\n--- Simulation Completed: Generated {frame_counter} frames ---")


def save_board(board: Board, pickle_path: str) -> None:
    with open(pickle_path, "wb") as f:
        pickle.dump(board, f)


def load_board(pickle_path: str) -> Board:
    with open(pickle_path, "rb") as f:
        return pickle.load(f)
