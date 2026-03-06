import os
import glob
from board import Board


def main() -> None:
    # 🧹 Clean up old SVG frames before starting
    for old_frame in glob.glob("frame_*.svg"):
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
