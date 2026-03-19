"""
Main entry point for the Monopoly game simulation.

This script handles the initial setup, including environment preparation
(creating and cleaning the output directory for SVG frames), prompting
the user for game parameters, initializing the board state from local JSON
data, and triggering the main game loop.
"""

import os
import glob
import random
import const as c
from board import Board


def read_num_players() -> int:
    """
    Prompt the user via standard input for the number of players.

    Continuously prompts the user (using recursion) until a valid integer
    within the configured bounds (2 to MAX_PLAYERS) is provided.

    Returns:
        int: The validated number of players for the game.
    """
    print(f"Enter number of players (2 - {c.MAX_PLAYERS}))")
    num = int(input())
    if num < 2 or num > c.MAX_PLAYERS:
        print("Invalid input, try again")
        return read_num_players()
    return num


def main() -> None:
    """
    Execute the core setup and main event loop of the game.

    This function ensures the 'frames' directory exists, clears out any
    leftover SVG files from previous runs to maintain a clean workspace,
    initializes the Board with the necessary data files, and starts the simulation.
    """
    # 0. Set the random seed for reproducibility.
    # This seed must be deleted if you want to have different games every time you run the program.
    random.seed(4)

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
