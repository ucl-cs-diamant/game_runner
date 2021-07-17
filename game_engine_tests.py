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
        deck = game_engine.Deck(
            [game_engine.Card("Relic", 5), game_engine.Card("Trap", "Snake")]
        )
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


class PlayerTestCase(unittest.TestCase):
    def test_player_creation_clean(self):
        player = game_engine.Player("123")

        self.assertEqual(player.chest, 0)
        self.assertEqual(player.pocket, 0)
        self.assertTrue(player.in_cave)
        self.assertTrue(player.continuing)

    def test_player_pickup_loot(self):
        player = game_engine.Player("123")

        pickup_amount = 10
        player.pickup_loot(10)

        self.assertEqual(player.pocket, pickup_amount)

    def test_player_leave_cave(self):
        player = game_engine.Player("123")

        chest_amount = player.chest

        pickup_amount = 10
        player.pickup_loot(pickup_amount)

        player.leave_cave()

        self.assertEqual(player.chest, chest_amount + pickup_amount)
        self.assertEqual(player.pocket, 0)
        self.assertFalse(player.continuing)
        self.assertFalse(player.in_cave)

    def test_player_kill(self):
        player = game_engine.Player("123")

        player.pickup_loot(10)
        
        player.kill_player()

        self.assertEqual(player.pocket, 0)
        self.assertFalse(player.in_cave)
        self.assertFalse(player.continuing)


if __name__ == "__main__":
    unittest.main()
