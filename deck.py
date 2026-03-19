"""
Deck management for Chance and Community Chest cards.

This module defines the `Deck` class, which handles loading card configurations
from a JSON file, instantiating the card objects, shuffling them, and managing
the draw/discard pile mechanics.
"""

import json
import random
from typing import TYPE_CHECKING
from card import build_card

if TYPE_CHECKING:
    from card import Card
    from board import Board


class Deck:
    """
    Represents a deck of drawable cards in the game.

    The deck acts as a queue where cards are drawn from the top (front of the list)
    and typically returned to the bottom (back of the list) after use.
    """

    _cards: list["Card"]

    def __init__(self, json_path: str, board: "Board"):
        """
        Initialize and shuffle the deck from a JSON configuration file.

        Args:
            json_path (str): The relative path to the JSON file containing card data.
            board (Board): The game board instance (passed to cards upon creation).
        """

        self._cards = []

        with open(json_path, "r", encoding="utf-8") as file:
            cards_data = json.load(file)

        for card_dict in cards_data:
            self._cards.append(build_card(card_dict))

        random.shuffle(self._cards)

    def draw(self) -> "Card":
        """
        Draw the top card from the deck.

        If the card is not a 'keepable' card (like a Get Out of Jail Free card), 
        it is immediately placed at the bottom of the deck to be reused later.

        Returns:
            Card: The card drawn from the top of the deck.
        """
        # Pop from index 0 to simulate drawing the top card of the deck
        card = self._cards.pop(0)

        # Standard cards go back to the bottom of the deck. 
        # Keepable cards stay with the player until played.
        if not card.keep_card:
            self._cards.append(card)

        return card
