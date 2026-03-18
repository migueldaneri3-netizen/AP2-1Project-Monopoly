import os
import glob
import random
import const as c
from board import Board
from yogi import read


def read_num_players() -> int:
    print(f"Enter number of players (2 - {c.MAX_PLAYERS}))")
    num = read(int)
    if num < 2 or num > c.MAX_PLAYERS:
        print("Invalid input, try again")
        return read_num_players()
    return num


def main() -> None:

    random.seed(2)

    # 1. Create the 'frames' directory if it doesn't exist
    os.makedirs("frames", exist_ok=True)

    # 2. Clean up the old SVGs inside that specific folder
    for old_frame in glob.glob("frames/frame_*.svg"):
        try:
            os.remove(old_frame)
        except OSError:
            pass

    num_players = read_num_players()

    board = Board(
        tiles_json_path="data/tiles.json",
        chance_json_path="data/chance.json",
        community_chest_json_path="data/community-chest.json",
        players_json_path="data/players.json",
        num_players=num_players,
    )

    board.play()


if __name__ == "__main__":
    main()
