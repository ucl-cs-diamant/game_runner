
import unittest

import random

import game_engine


class TestEngineInterface:
    def __init__(self):
        self.players = range(6)

    def check_dead_players(self):
        pass

    async def init_game(self):
        pass

    def roll_decision(self):
        decision = random.randint(0, 1)
        return decision

    async def request_decisions(self):
        decisions = []
        for i in range(6):
            decisions.append({"decision": self.roll_decision()})
        decisions = {player_id: decisions[i] for i, player_id in enumerate(range(6))}
        return decisions

    def report_outcome(self, winning_players: list):
        pass


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
    def test_deck_constructor_clean(self):
        deck = game_engine.Deck()
        self.assertEqual(len(deck.cards), 35)

        relics = [card for card in deck.cards if card.card_type == "Relic"]
        self.assertEqual(len(relics), 5)

        traps = [card for card in deck.cards if card.card_type == "Trap"]
        self.assertEqual(len(traps), 15)

        treasures = [card for card in deck.cards if card.card_type == "Treasure"]
        self.assertEqual(len(treasures), 15)

    def test_deck_constructor_exclusion(self):
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


class PlayerTestCase(unittest.TestCase):
    def test_player_creation_clean(self):
        player = game_engine.Player(123)

        self.assertEqual(player.chest, 0)
        self.assertEqual(player.pocket, 0)
        self.assertTrue(player.in_cave)
        self.assertTrue(player.continuing)

    def test_player_pickup_loot(self):
        player = game_engine.Player(123)
        match_history = game_engine.MatchHistory()

        pickup_amount = 10
        player.pickup_loot(10, match_history)

        self.assertEqual(player.pocket, pickup_amount)
        self.assertEqual(str(match_history),
                         "[{'event_type': 'player_pickup', 'content': {'player_id': 123, 'pocket': 0, 'amount': 10}}]")

    def test_player_leave_cave(self):
        player = game_engine.Player(123)
        match_history = game_engine.MatchHistory()

        chest_amount = player.chest

        pickup_amount = 10
        player.pickup_loot(pickup_amount, match_history)

        player.leave_cave(match_history)

        self.assertEqual(player.chest, chest_amount + pickup_amount)
        self.assertEqual(player.pocket, 0)
        self.assertFalse(player.continuing)
        self.assertFalse(player.in_cave)

        self.assertEqual(str(match_history[1]),
                         "{'event_type': 'player_leaves', 'content': {'player_id': 123, 'pocket': 10, 'chest': 0}}")

    def test_player_kill(self):
        player = game_engine.Player(123)
        player.chest = 5
        match_history = game_engine.MatchHistory()

        player.pickup_loot(10, match_history)

        player.kill_player(match_history)

        self.assertEqual(player.pocket, 0)
        self.assertEqual(player.chest, 5)
        self.assertFalse(player.in_cave)
        self.assertFalse(player.continuing)

        self.assertEqual(str(match_history[1]),
                         "{'event_type': 'player_death', 'content': {'player_id': 123, 'pocket': 10}}")


def create_test_board():
    board = game_engine.Board()
    match_history = game_engine.MatchHistory()
    board.add_card(game_engine.Card("Treasure", 10), match_history)
    board.add_card(game_engine.Card("Relic", 5), match_history)
    board.add_card(game_engine.Card("Trap", "Snake"), match_history)
    board.add_card(game_engine.Card("Trap", "Ram"), match_history)
    board.add_card(game_engine.Card("Trap", "Snake"), match_history)
    return board, match_history


class BoardTestCase(unittest.TestCase):
    def test_board_constructor(self):
        board = game_engine.Board()

        self.assertEqual(board.route, [])
        self.assertEqual(board.double_trap, False)
        self.assertEqual(board.relics_picked, 0)
        self.assertEqual(board.excluded_cards, [])

    def test_board_str(self):
        board = game_engine.Board()

        self.assertEqual(board.__str__(), "[]")

    def test_board_add_card(self):
        board, match_history = create_test_board()

        self.assertEqual(board.route[0].card_type, "Treasure")
        self.assertEqual(board.route[1].card_type, "Relic")
        self.assertEqual(board.route[2].card_type, "Trap")
        self.assertEqual(board.excluded_cards[0].value, 5)
        self.assertEqual(board.excluded_cards[1].value, "Snake")
        self.assertEqual(board.relics_picked, 1)
        self.assertTrue(board.double_trap)

        self.assertEqual(str(match_history[0]),
                         "{'event_type': 'board_add_card', 'content': {'card_type': 'Treasure', 'value': 10}}")
        self.assertEqual(str(match_history[1]),
                         "{'event_type': 'board_add_card', 'content': {'card_type': 'Relic', 'value': 5}}")
        self.assertEqual(str(match_history[2]),
                         "{'event_type': 'board_add_card', 'content': {'card_type': 'Trap', 'value': 'Snake'}}")

    def test_board_add_relics(self):
        board = game_engine.Board()
        match_history = game_engine.MatchHistory()
        board.add_card(game_engine.Card("Relic", 5), match_history)
        board.add_card(game_engine.Card("Relic", 5), match_history)
        board.add_card(game_engine.Card("Relic", 5), match_history)
        board.add_card(game_engine.Card("Relic", 5), match_history)
        board.add_card(game_engine.Card("Relic", 5), match_history)

        for i in range(3):
            self.assertEqual(board.route[i].value, 5)

        self.assertEqual(board.route[3].value, 10)
        self.assertEqual(board.route[4].value, 10)

    def test_board_reset_path(self):
        board, _ = create_test_board()

        board.reset_path()
        self.assertEqual(board.route, [])
        self.assertFalse(board.double_trap)
        self.assertEqual(board.relics_picked, 1)
        self.assertEqual(board.excluded_cards[0].value, 5)


class AdvancementPhaseTestCase(unittest.TestCase):
    def setUp(self):
        self.deck = game_engine.Deck()
        self.players = []
        for i in range(6):
            self.players.append(game_engine.Player(i))
        self.board = game_engine.Board()
        self.first_card = self.deck.cards[0]
        self.match_history = game_engine.MatchHistory()

    def test_handle_treasure_loot(self):
        card = game_engine.Card("Treasure", 7)

        game_engine.handle_treasure_loot(card, 0, self.players, self.match_history)

        self.assertEqual(card.value, 1)

        for player in self.players:
            self.assertEqual(player.pocket, 1)

        self.assertEqual(str(self.match_history[0]),
                         "{'event_type': 'board_change_card', "
                         "'content': {'card_index': 0, 'card_type': 'Treasure', 'value': 1}}")

    def test_advance_no_actives(self):
        for player in self.players:
            player.in_cave = False

        outcome = game_engine.advancement_phase(self.deck, self.players, self.board, self.match_history)

        self.assertTrue(outcome)
        self.assertEqual(self.first_card, self.board.route[0])

    def test_advance_trap_trigger(self):
        self.deck.cards[0] = game_engine.Card("Trap", "Snake")
        self.board.route.append(game_engine.Card("Trap", "Snake"))

        outcome = game_engine.advancement_phase(self.deck, self.players, self.board, self.match_history)

        self.assertTrue(outcome)
        for player in self.players:
            self.assertFalse(player.in_cave)

    def test_advance_treasure(self):
        self.deck.cards[0] = game_engine.Card("Treasure", 7)

        outcome = game_engine.advancement_phase(self.deck, self.players, self.board, self.match_history)

        self.assertFalse(outcome)

        for player in self.players:
            self.assertEqual(player.pocket, 1)


class HandleLeavingPlayersTestCase(unittest.TestCase):
    def setUp(self):
        self.board = game_engine.Board()
        self.players = []
        for i in range(6):
            self.players.append(game_engine.Player(i))
        self.match_history = game_engine.MatchHistory()

    def test_handle_leaving_players_zero(self):
        self.board.add_card(game_engine.Card("Treasure", 6), self.match_history)

        game_engine.handle_leaving_players(0, [], self.board, self.match_history)

        self.assertEqual(self.board.route[0].value, 6)

    def test_handle_leaving_players_treasure(self):
        self.board.add_card(game_engine.Card("Treasure", 6), self.match_history)

        game_engine.handle_leaving_players(6, self.players, self.board, self.match_history)

        self.assertEqual(self.board.route[0].value, 0)

        for player in self.players:
            self.assertEqual(player.pocket, 1)

    def test_handle_leaving_players_relic(self):
        self.board.add_card(game_engine.Card("Relic", 5), self.match_history)

        game_engine.handle_leaving_players(2, self.players[:2], self.board, self.match_history)

        self.assertEqual(self.board.route[0].value, 5)
        self.assertEqual(self.players[0].pocket, 0)
        self.assertEqual(self.players[1].pocket, 0)

        game_engine.handle_leaving_players(1, [self.players[0]], self.board, self.match_history)

        self.assertEqual(self.board.route[0].value, 0)
        self.assertEqual(self.players[0].pocket, 5)

        self.assertEqual(str(self.match_history[2]),
                         "{'event_type': 'board_change_card', "
                         "'content': {'card_index': 0, 'card_type': 'Relic', 'value': 0}}")


class DecisionPhaseTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.board = game_engine.Board()
        self.players = []
        for i in range(6):
            self.players.append(game_engine.Player(i))
        self.ei = TestEngineInterface()
        self.match_history = game_engine.MatchHistory()

    async def test_correct_players_leaving(self):
        self.players[0].in_cave = False
        original_value = 5
        self.board.add_card(game_engine.Card("Treasure", original_value), self.match_history)

        random.seed(0)

        await game_engine.decision_phase(self.players, self.board, self.ei, self.match_history)

        self.assertEqual(self.players[0].chest, 0)

        leaving_players = [player for player in self.players[1:] if player.continuing is False]
        self.assertEqual(self.board.route[0].value, original_value % len(leaving_players))
        self.assertEqual((len(self.match_history) - 2) / 2, len(leaving_players))

        for left_player in leaving_players:
            self.assertFalse(left_player.in_cave)
            self.assertEqual(left_player.chest, original_value // len(leaving_players))


def create_game_engine_self_state():
    deck = game_engine.Deck()
    players = []
    for i in range(6):
        players.append(game_engine.Player(i))
    board = game_engine.Board()
    ei = TestEngineInterface()
    match_history = game_engine.MatchHistory()

    return deck, players, board, ei, match_history


class SingleTurnTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.deck, self.players, self.board, self.ei, self.match_history = create_game_engine_self_state()

    async def test_failure_state_traps(self):
        self.deck.cards[0] = game_engine.Card("Trap", "Snake")
        self.board.route.append(game_engine.Card("Trap", "Snake"))

        outcome = await game_engine.single_turn(self.deck, self.players, self.board, self.ei, self.match_history)

        self.assertEqual(str(self.match_history[0]),
                         "{'event_type': 'board_trap_trigger', "
                         "'content': {'card_type': 'Trap', 'value': 'Snake'}}")

        self.assertTrue(outcome)

    async def test_failure_state_players(self):
        for player in self.players:
            player.in_cave = False

        outcome = await game_engine.single_turn(self.deck, self.players, self.board, self.ei, self.match_history)

        self.assertTrue(outcome)

    async def test_passing_state(self):
        outcome = await game_engine.single_turn(self.deck, self.players, self.board, self.ei, self.match_history)

        self.assertFalse(outcome)


class RunPathTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.deck, self.players, self.board, self.ei, self.match_history = create_game_engine_self_state()

    async def test_run_path_reset_failure(self):
        self.deck.cards[0] = game_engine.Card("Trap", "Snake")
        self.deck.cards[1] = game_engine.Card("Trap", "Snake")

        await game_engine.run_path(self.deck, self.players, self.board, self.ei, self.match_history)

        self.assertEqual(self.board.route, [])
        self.assertFalse(self.board.double_trap)

        for player in self.players:
            self.assertEqual(player.pocket, 0)
            self.assertTrue(player.in_cave)
            self.assertTrue(player.continuing)


class SetupGameTestCase(unittest.TestCase):     # todo: expand upon later
    def test_return_types(self):
        deck, board = game_engine.setup_game()

        self.assertEqual(type(deck), game_engine.Deck)
        self.assertEqual(type(board), game_engine.Board)


class RunGameTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_run_game_return_type(self):
        ei = TestEngineInterface()

        winner_list, match_history = await game_engine.run_game(ei)

        for winner in winner_list:
            self.assertEqual(type(winner), int)

        self.assertEqual(str(match_history[0]),
                         "{'event_type': 'new_path', "
                         "'content': {'path_num': 0}}")


if __name__ == '__main__':
    unittest.main()
