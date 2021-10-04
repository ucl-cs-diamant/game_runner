import asyncio
import unittest
import random
from unittest import mock

import game_engine
from game_engine import MatchEvent


class TestEngineInterface:
    def __init__(self, *_):
        self.players = range(6)

    def init_game(self):
        pass

    async def init_players(self):
        pass

    # def check_dead_players(self):
    #     pass
    #
    # async def init_game(self):
    #     pass

    @staticmethod
    async def request_decisions(_):
        decisions = []
        for i in range(6):
            decisions.append({"decision": random.randint(0, 1)})
        decisions = {player_id: decisions[i] for i, player_id in enumerate(range(6))}
        return decisions

    # def report_outcome(self, winning_players: list):
    #     pass


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


def get_or_create_event_loop():
    # try:
    #     loop = asyncio.get_event_loop()
    #     print("got loop from get")
    #     return loop
    # except RuntimeError as ex:
    #     if "There is no current event loop in thread" in str(ex):
    #         print("creating new loop")
    #         loop = asyncio.new_event_loop()
    #         asyncio.set_event_loop(loop)
    #         return asyncio.get_event_loop()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


# @mock.patch('asyncio.get_event_loop', get_or_create_event_loop)
class AdvancementPhaseTestCase(unittest.TestCase):
    @mock.patch('diamant_game_interface.EngineInterface', TestEngineInterface)
    def setUp(self):
        # with mock.patch('diamant_game_interface.OnlineEngineInterface', TestEngineInterface):
        self.game_engine = game_engine.GameEngine()

        self.deck = game_engine.Deck()
        self.players = []
        for i in range(6):
            self.players.append(game_engine.Player(i))
        self.board = game_engine.Board()
        self.first_card = self.deck.cards[0]
        self.match_history = game_engine.MatchHistory()

    def test_handle_treasure_loot(self):
        card = game_engine.Card("Treasure", 7)

        self.game_engine.handle_treasure_loot(card, 0, self.players)

        self.assertEqual(card.value, 1)

        for player in self.players:
            self.assertEqual(player.pocket, 1)

        self.assertEqual(str(self.game_engine.match_history[0]),
                         "{'event_type': 'board_change_card', "
                         "'content': {'card_index': 0, 'card_type': 'Treasure', 'value': 1}}")

    def test_advance_no_actives(self):
        for player in self.players:
            player.in_cave = False

        outcome = self.game_engine.advancement_phase(self.deck, self.players, self.board)

        self.assertTrue(outcome)
        self.assertEqual(self.first_card, self.board.route[0])

    def test_advance_trap_trigger(self):
        self.deck.cards[0] = game_engine.Card("Trap", "Snake")
        self.board.route.append(game_engine.Card("Trap", "Snake"))

        outcome = self.game_engine.advancement_phase(self.deck, self.players, self.board)

        self.assertTrue(outcome)
        for player in self.players:
            self.assertFalse(player.in_cave)

    def test_advance_treasure(self):
        self.deck.cards[0] = game_engine.Card("Treasure", 7)

        outcome = self.game_engine.advancement_phase(self.deck, self.players, self.board)

        self.assertFalse(outcome)

        for player in self.players:
            self.assertEqual(player.pocket, 1)


# @mock.patch('asyncio.get_event_loop', get_or_create_event_loop)
class HandleLeavingPlayersTestCase(unittest.TestCase):
    @mock.patch('diamant_game_interface.EngineInterface', TestEngineInterface)
    def setUp(self):
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        self.loop = get_or_create_event_loop()
        # asyncio.set_event_loop(self.loop)

        self.game_engine = game_engine.GameEngine()

        self.board = game_engine.Board()
        self.players = []
        for i in range(6):
            self.players.append(game_engine.Player(i))
        self.match_history = game_engine.MatchHistory()

    def tearDown(self) -> None:
        self.loop.close()

    def test_handle_leaving_players_zero(self):
        self.board.add_card(game_engine.Card("Treasure", 6), self.match_history)

        self.game_engine.handle_leaving_players(0, [], self.board)

        self.assertEqual(self.board.route[0].value, 6)

    def test_handle_leaving_players_treasure(self):
        self.board.add_card(game_engine.Card("Treasure", 6), self.match_history)

        self.game_engine.handle_leaving_players(6, self.players, self.board)

        self.assertEqual(self.board.route[0].value, 0)

        for player in self.players:
            self.assertEqual(player.pocket, 1)

    def test_handle_leaving_players_relic(self):
        self.board.add_card(game_engine.Card("Relic", 5), self.game_engine.match_history)

        self.game_engine.handle_leaving_players(2, self.players[:2], self.board)

        self.assertEqual(self.board.route[0].value, 5)
        self.assertEqual(self.players[0].pocket, 0)
        self.assertEqual(self.players[1].pocket, 0)

        self.game_engine.handle_leaving_players(1, [self.players[0]], self.board)

        self.assertEqual(self.board.route[0].value, 0)
        self.assertEqual(self.players[0].pocket, 5)

        self.assertEqual(str(self.game_engine.match_history[2]),
                         "{'event_type': 'board_change_card', "
                         "'content': {'card_index': 0, 'card_type': 'Relic', 'value': 0}}")


class TestExceptionHandling(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = get_or_create_event_loop()

    def tearDown(self) -> None:
        self.loop.close()

    def test_missing_gameserver_address(self):
        with self.assertRaises(ValueError):
            game_engine.GameEngine()


class DecisionPhaseTestCase(unittest.IsolatedAsyncioTestCase):
    @mock.patch('diamant_game_interface.EngineInterface', TestEngineInterface)
    def setUp(self):
        self.game_engine = game_engine.GameEngine()

        self.board = game_engine.Board()
        self.players = []
        for i in range(6):
            self.players.append(game_engine.Player(i))
        # self.ei = TestEngineInterface()
        self.match_history = game_engine.MatchHistory()

    def test_correct_players_leaving(self):
        self.players[0].in_cave = False
        original_value = 5
        self.board.add_card(game_engine.Card("Treasure", original_value), self.game_engine.match_history)

        random.seed(0)

        self.game_engine.decision_phase(self.players, self.board)

        self.assertEqual(self.players[0].chest, 0)

        leaving_players = [player for player in self.players[1:] if player.continuing is False]
        self.assertEqual(self.board.route[0].value, original_value % len(leaving_players))
        # self.assertEqual((len(self.game_engine.match_history) - 2) / 2, len(leaving_players))
        self.assertEqual(len(self.game_engine.match_history), 4)
        self.assertEqual(len(leaving_players), 1)

        for left_player in leaving_players:
            self.assertFalse(left_player.in_cave)
            self.assertEqual(left_player.chest, original_value // len(leaving_players))

    async def test_game_state_empty(self):
        self.game_engine.match_history.get_updates()
        self.assertEqual([], self.match_history.get_updates())

    async def test_game_state_updates(self):
        self.match_history.add_event(MatchEvent.CHANGE_CARD, {"card_index": 1,
                                                              "card_type": "Treasure",
                                                              "value": 5})
        self.assertEqual([{'event_type': 'board_change_card',
                           'content':
                               {'card_index': 1,
                                'card_type': 'Treasure',
                                'value': 5}
                           }],
                         self.match_history.get_updates())


def create_game_engine_self_state():
    deck = game_engine.Deck()
    players = []
    for i in range(6):
        players.append(game_engine.Player(i))
    board = game_engine.Board()
    # ei = TestEngineInterface()
    match_history = game_engine.MatchHistory()

    # return deck, players, board, ei, match_history
    return deck, players, board, match_history


class SingleTurnTestCase(unittest.IsolatedAsyncioTestCase):
    @mock.patch('diamant_game_interface.EngineInterface', TestEngineInterface)
    def setUp(self):
        # self.deck, self.players, self.board, self.ei, self.match_history = create_game_engine_self_state()
        self.deck, self.players, self.board, self.match_history = create_game_engine_self_state()
        self.game_engine = game_engine.GameEngine()

    def test_failure_state_traps(self):
        self.deck.cards[0] = game_engine.Card("Trap", "Snake")
        self.board.route.append(game_engine.Card("Trap", "Snake"))

        outcome = self.game_engine.single_turn(self.deck, self.players, self.board)

        self.assertEqual(str(self.game_engine.match_history[0]),
                         "{'event_type': 'board_trap_trigger', "
                         "'content': {'card_type': 'Trap', 'value': 'Snake'}}")

        self.assertTrue(outcome)

    def test_failure_state_players(self):
        for player in self.players:
            player.in_cave = False

        outcome = self.game_engine.single_turn(self.deck, self.players, self.board)

        self.assertTrue(outcome)

    def test_passing_state(self):
        outcome = self.game_engine.single_turn(self.deck, self.players, self.board)

        self.assertFalse(outcome)


class RunPathTestCase(unittest.IsolatedAsyncioTestCase):
    @mock.patch('diamant_game_interface.EngineInterface', TestEngineInterface)
    def setUp(self):
        self.loop = get_or_create_event_loop()
        self.deck, self.players, self.board, self.match_history = create_game_engine_self_state()
        self.game_engine = game_engine.GameEngine()

    def tearDown(self) -> None:
        self.loop.close()

    def test_run_path_reset_failure(self):
        self.deck.cards[0] = game_engine.Card("Trap", "Snake")
        self.deck.cards[1] = game_engine.Card("Trap", "Snake")

        self.game_engine.run_path(self.deck, self.players, self.board)

        self.assertEqual(self.board.route, [])
        self.assertFalse(self.board.double_trap)

        for player in self.players:
            self.assertEqual(player.pocket, 0)
            self.assertTrue(player.in_cave)
            self.assertTrue(player.continuing)


class SetupGameTestCase(unittest.TestCase):  # todo: expand upon later
    def setUp(self) -> None:
        self.loop = get_or_create_event_loop()

    def tearDown(self) -> None:
        self.loop.close()

    @mock.patch('diamant_game_interface.EngineInterface', TestEngineInterface)
    def test_return_types(self):
        ge = game_engine.GameEngine()
        deck, board = ge.setup_game()

        self.assertEqual(type(deck), game_engine.Deck)
        self.assertEqual(type(board), game_engine.Board)


class RunGameTestCase(unittest.IsolatedAsyncioTestCase):
    @mock.patch('diamant_game_interface.EngineInterface', TestEngineInterface)
    def setUp(self) -> None:
        # loop = asyncio.new_event_loop()
        # try:
        #     loop = asyncio.get_event_loop()
        # except asyncio.
        # asyncio.set_event_loop(loop)
        self.loop = get_or_create_event_loop()

        self.game_engine = game_engine.GameEngine()

    def tearDown(self) -> None:
        self.loop.close()

    def test_run_game_return_type(self):
        winner_list = self.game_engine.run_game()

        for winner in winner_list:
            self.assertEqual(type(winner), int)

        self.assertEqual(str(self.game_engine.match_history[0]),
                         "{'event_type': 'new_path', "
                         "'content': {'path_num': 0}}")


class OfflineModeEngineTest(unittest.TestCase):
    @staticmethod
    def decision_maker(_):
        print("yp")
        return True

    @mock.patch('diamant_game_interface.OfflineEngineInterface')
    def test_get_decisions(self, patched: mock.MagicMock):
        cls_inst = mock.MagicMock()
        cls_inst.request_decisions.return_value = 'yep'
        patched.return_value = cls_inst

        ge = game_engine.GameEngine(offline_decision_maker=self.decision_maker)
        ge.event_loop = None  # attribute error "'NoneType' object has no attribute 'run_until_complete'" if bad
        ge.get_decisions()

        self.assertTrue(ge.offline)
        cls_inst.request_decisions.assert_called()


if __name__ == '__main__':
    unittest.main()
