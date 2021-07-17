import unittest
import game_engine


class CardTestCase(unittest.TestCase):
    def test_card_constructor(self):
        treasure_card = game_engine.Card("Treasure", 100)
        relic_card = game_engine.Card("Relic", 5)
        trap_card = game_engine.Card("Trap", "Snake")

        self.assertEqual(treasure_card.card_type, "Treasure")
        self.assertEqual(treasure_card.value, 100)

        self.assertEqual(relic_card.card_type, "Relic")
        self.assertEqual(relic_card.value, 5)

        self.assertEqual(trap_card.card_type, "Trap")
        self.assertEqual(trap_card.value, "Snake")

    def test_card_str(self):
        card = game_engine.Card("Treasure", 100)
        self.assertEqual("Treasure 100", card.__str__())


class DeckTestCase(unittest.TestCase):
    def test_deck_generation_clean(self):
        deck = game_engine.Deck()
        self.assertEqual(len(deck.cards), 35)

        relics = [card for card in deck.cards if card.card_type == "Relic"]
        self.assertEqual(len(relics), 5)

        traps = [card for card in deck.cards if card.card_type == "Trap"]
        self.assertEqual(len(traps), 15)

        treasures = [card for card in deck.cards if card.card_type == "Treasure"]
        self.assertEqual(len(treasures), 15)

    def test_deck_generation_exclusion(self):
        deck = game_engine.Deck([game_engine.Card("Relic", 5), game_engine.Card("Trap", "Snake")])
        self.assertEqual(len(deck.cards), 33)

        relics = [card for card in deck.cards if card.card_type == "Relic"]
        self.assertEqual(len(relics), 4)

        traps = [card for card in deck.cards if card.card_type == "Trap"]
        self.assertEqual(len(traps), 14)

        treasures = [card for card in deck.cards if card.card_type == "Treasure"]
        self.assertEqual(len(treasures), 15)

    def test_deck_pick_card(self):
        deck = game_engine.Deck()
        first_card = deck.cards[0]
        second_card = deck.cards[1]
        picked_card = deck.pick_card()

        self.assertEqual(first_card, picked_card)
        self.assertEqual(second_card, deck.cards[0])


if __name__ == '__main__':
    unittest.main()
