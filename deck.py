import json
import random
from typing import TYPE_CHECKING
from card import build_card

if TYPE_CHECKING:
    from card import Card
    from board import Board


class Deck:
    """Pas 8.2: Implementar la classe Deck amb barreja i roba."""

    def __init__(self, json_path: str, board: "Board"):
        self._cards: list["Card"] = []

        with open(json_path, "r", encoding="utf-8") as file:
            cards_data = json.load(file)

        for card_dict in cards_data:
            self._cards.append(build_card(card_dict))

        random.shuffle(self._cards)

    def draw(self) -> "Card":
        """Draws the top card. If it's not a 'keep' card, it goes to the bottom."""
        card = self._cards.pop(0)

        if not card.keep_card:
            self._cards.append(card)

        return card
