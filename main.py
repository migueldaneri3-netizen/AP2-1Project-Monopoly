import os
import glob
import random
from board import Board


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

    board = Board(
        tiles_json_path="data/tiles.json",
        chance_json_path="data/chance.json",
        community_chest_json_path="data/community-chest.json",
        players_json_path="data/players.json",
    )

    board.play()


if __name__ == "__main__":
    main()
