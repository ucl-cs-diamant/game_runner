import asyncio
from collections.abc import Callable
from enum import Enum
import logging
import numpy as np
import os
from typing import Union


def generate_deck(exclusions: Union[list, None]) -> list:
    card_deck = {
        Card("Treasure", 5):  2,
        Card("Treasure", 9):  1,
        Card("Treasure", 14): 1,
        Card("Treasure", 3):  1,
        Card("Treasure", 17): 1,
        Card("Treasure", 2):  1,
        Card("Treasure", 7):  2,
        Card("Treasure", 1):  1,
        Card("Treasure", 11): 2,
        Card("Treasure", 4):  1,
        Card("Treasure", 15): 1,
        Card("Treasure", 13): 1,

        Card("Relic", 5): 5,

        Card("Trap", "Spider"):  3,
        Card("Trap", "Snake"):   3,
        Card("Trap", "Lava"):    3,
        Card("Trap", "Boulder"): 3,
        Card("Trap", "Ram"):     3,
    }

    card_deck = [elem for card, count in card_deck.items() for elem in [card] * count]

    if exclusions is None:
        return card_deck

    for excluded_card in exclusions:
        for card in card_deck:
            if card.card_type == excluded_card.card_type and card.value == excluded_card.value:
                card_deck.remove(card)
                break  # find a matching card, remove it once, and immediately break
    return card_deck


class MatchEvent(Enum):
    """
        match history = [match_event]
        match_event = {event_type:item, content:{}}
        player_pickup.keys() = [player_id, pocket, amount]
        player_death.keys() = [player_id, pocket]
        player_leaves.keys() = [player_id, pocket, chest]
        NOTE: all player values are snapshots of before the event happens

        board_add_card.keys() = [card_type, value]

        board_change_card.keys() = [card_index, card_type, value]
        NOTE: card_index = index of board.route where card is located

        board_trap_trigger.keys() = [card_type, value]
        new_path.keys() = [path_num]
    """
    LEAVE_CAVE = "player_leaves"
    KILL_PLAYER = "player_death"
    PICKUP_LOOT = "player_pickup"
    TRIGGER_TRAP = "board_trap_trigger"
    ADD_CARD = "board_add_card"
    CHANGE_CARD = "board_change_card"
    NEW_PATH = "new_path"


class MatchHistory(list):
    def __init__(self):
        super().__init__()
        self.update_pointer = 0

    def add_event(self, event_type: MatchEvent, event_data: dict):  # couldn't find a best practices document for this
        self.append({"event_type": event_type.value, "content": event_data})

    def get_updates(self):
        if self.update_pointer >= len(self):  # should never happen, events must happen between decision requests
            return []

        start_of_updates = self.update_pointer
        self.update_pointer = len(self)
        return self[start_of_updates:]


class Card:
    def __init__(self, card_type, value):
        self.card_type = card_type
        self.value = value

    def __str__(self):
        return str(self.card_type + " " + str(self.value))


class Deck:
    def __init__(self, exclusions=None):  # generate a full deck and shuffle it
        self.cards = generate_deck(exclusions)
        self.shuffle_deck()

    def __str__(self):
        # iterate over all cards and make a list of names and values
        return str([(card_name.card_type + " " + str(card_name.value)) for card_name in self.cards])

    def shuffle_deck(self):
        np.random.shuffle(self.cards)

    def pick_card(self):  # pick a card from the first element and remove it from the deck
        picked_card = self.cards[0]
        self.cards.pop(0)
        return picked_card


class Player:
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.chest = 0
        self.pocket = 0  # how much a player has on hand mid exploration
        self.in_cave = True  # whether a player is currently in the cave
        self.continuing = True  # the players decision to continue

    def leave_cave(self, match_history: MatchHistory):  # player leaves cave safely and stores their loot
        match_history.add_event(MatchEvent.LEAVE_CAVE,
                                {"player_id": self.player_id, "pocket": self.pocket, "chest": self.chest})
        self.in_cave = False
        self.continuing = False
        self.chest += self.pocket
        self.pocket = 0

    def kill_player(self, match_history: MatchHistory):
        # player dies in the cave, loot is lost, and values reset to normal
        match_history.add_event(MatchEvent.KILL_PLAYER, {"player_id": self.player_id, "pocket": self.pocket})
        self.pocket = 0
        self.in_cave = False
        self.continuing = False

    def pickup_loot(self, amount, match_history: MatchHistory):  # player picks up some loot
        match_history.add_event(MatchEvent.PICKUP_LOOT, {"player_id": self.player_id, "pocket": self.pocket,
                                                         "amount": amount})
        self.pocket += amount

    def reset_player(self):  # reset a player for the next path
        self.pocket = 0
        self.in_cave = True
        self.continuing = True


class Board:
    def __init__(self):
        self.route = []
        self.double_trap = False
        self.excluded_cards = []
        self.relics_picked = 0  # note: relics are counted when placed in the route

    def __str__(self):
        return str(self.route)

    # pick a card, if its another trap card, set double_trap to the trap card and kill the players at some point
    def add_card(self, card, match_history: MatchHistory):
        if card.card_type == "Trap":  # Traps need to checked before being added for logic reasons
            for board_card in self.route:
                if card.value == board_card.value:
                    self.double_trap = True
                    match_history.add_event(MatchEvent.TRIGGER_TRAP, {"card_type": card.card_type,
                                                                      "value": card.value})
                    self.excluded_cards.append(card)
                    break

        self.route.append(card)

        if card.card_type == "Relic":  # Relics can be changed after adding neatly
            self.relics_picked += 1
            self.excluded_cards.append(card)
            if self.relics_picked > 3:  # 4th and 5th relic have 10 value
                self.route[-1].value = 10

        match_history.add_event(MatchEvent.ADD_CARD, {"card_type": card.card_type, "value": card.value})

    def reset_path(self):  # intentionally left out triggered doubles so it carries between paths
        self.route = []
        self.double_trap = False


class GameEngine:
    def __init__(self, offline_decision_maker: Callable = None):

        self.match_history = MatchHistory()
        self.offline = offline_decision_maker is not None

        if offline_decision_maker is None:
            from diamant_game_interface import EngineInterface
            self.event_loop = asyncio.get_event_loop()
            self.engine_interface = EngineInterface(os.environ.get("GAMESERVER_HOST"),
                                                    os.environ.get("GAMESERVER_PORT"))

            self.engine_interface.init_game()
            self.event_loop.run_until_complete(self.engine_interface.init_players())
            return

        from diamant_game_interface import OfflineEngineInterface
        self.engine_interface = OfflineEngineInterface(offline_decision_maker)
        self.engine_interface.init_players()

    @staticmethod
    def setup_game():
        initial_deck = Deck()
        empty_board = Board()
        return initial_deck, empty_board

    def get_decisions(self):
        if self.offline:
            return self.engine_interface.request_decisions(self.match_history.get_updates())
        return self.event_loop.run_until_complete(
            self.engine_interface.request_decisions(self.match_history.get_updates()))

    def handle_treasure_loot(self, board_card, card_index, players):

        # board_card is either the new card, or the card on the route as the players are leaving
        # players are the players who decided to leave or the remaining active players
        no_players = len(players)
        obtained_loot = board_card.value // no_players  # do integer division of the loot
        board_card.value = board_card.value % no_players  # set new value to reflect taken loot
        self.match_history.add_event(MatchEvent.CHANGE_CARD, {"card_index": card_index,
                                                              "card_type": board_card.card_type,
                                                              "value": board_card.value})

        for player in players:  # go through the provided player list and give them the divided loot
            player.pickup_loot(obtained_loot, self.match_history)

    def advancement_phase(self, path_deck, path_player_list, path_board):
        path_board.add_card(path_deck.pick_card(), self.match_history)

        active_players = [player for player in path_player_list if player.in_cave]
        no_active_players = len(active_players)
        if no_active_players == 0:
            return True  # return immediately to move to the next expedition

        last_route = path_board.route[-1]

        if last_route.card_type == "Treasure":
            self.handle_treasure_loot(last_route, path_board.route.index(last_route), active_players)

        if last_route.card_type == "Relic":  # this IF is here for sheer readability and does nothing
            pass

        if last_route.card_type == "Trap":
            if path_board.double_trap:  # if its the second trap, kill all active players
                for player in active_players:  # go through the  player list and kill all the remaining active players
                    player.kill_player(self.match_history)
                return True  # return a true flag to show the expedition should fail
        else:
            return False

    def make_decisions(self, path_player_list):  # actually make the players make a decision
        # player_decisions = asyncio.run(ei.request_decisions(match_history.get_updates()))

        # player_decisions = self.event_loop.run_until_complete(
        #     self.engine_interface.request_decisions(self.match_history.get_updates()))

        player_decisions = self.get_decisions()

        for player in path_player_list:
            player.continuing = player_decisions[player.player_id]["decision"]

    def handle_leaving_players(self, no_leaving_players, leaving_players, path_board):
        # function that handles card values and loot distribution upon leaving
        if no_leaving_players > 0:
            for board_card in path_board.route:
                if board_card.card_type == "Treasure":  # split loot evenly between players on treasure cards
                    self.handle_treasure_loot(board_card, path_board.route.index(board_card), leaving_players)

                # check if there is a relic to pick up (maybe pointless but it saves running the extra code 9/10 times)
                if board_card.card_type == "Relic" and board_card.value != 0:
                    if no_leaving_players == 1:
                        for player in leaving_players:
                            player.pickup_loot(board_card.value, self.match_history)
                            board_card.value = 0
                            self.match_history.add_event(MatchEvent.CHANGE_CARD,
                                                         {"card_index": path_board.route.index(board_card),
                                                          "card_type": board_card.card_type,
                                                          "value": board_card.value})

                if board_card.card_type == "Trap":  # dont care about traps
                    pass

    def decision_phase(self, path_player_list, path_board):
        self.make_decisions(path_player_list)

        # leaving players leaving and number of leaving players
        leaving_players = [player for player in path_player_list if player.in_cave and not player.continuing]
        no_leaving_players = len(leaving_players)

        # split the loot evenly between all leaving players, if one player is leaving, collect the relics
        self.handle_leaving_players(no_leaving_players, leaving_players, path_board)

        # once the board calculations are done, the players need to actually leave the cave
        for player in leaving_players:
            player.leave_cave(self.match_history)

    def single_turn(self, path_deck, path_player_list, path_board):
        # advancement phase
        expedition_failed = self.advancement_phase(path_deck, path_player_list, path_board)
        if expedition_failed:  # propagate the failure up
            return True
        # decision phase
        self.decision_phase(path_player_list, path_board)
        return False

    def run_path(self, deck, player_list, board):
        # runs through a path until all players leave or the run dies
        path_complete = False
        while not path_complete:
            path_complete = self.single_turn(deck, player_list, board)
        board.reset_path()  # reset board for a new path
        for player in player_list:  # reset all players so they are able to participate in the next path
            player.reset_player()

    def run_game(self):  # run a full game of diamant
        deck, board = self.setup_game()
        player_list = [Player(player_id) for player_id in self.engine_interface.players]

        for path_num in range(5):  # do 5 paths
            self.match_history.add_event(MatchEvent.NEW_PATH, {"path_num": path_num})
            self.run_path(deck, player_list, board)
            excluded_cards = board.excluded_cards
            for relic_count in range(board.relics_picked):  # add an exclusion for every picked relic
                excluded_cards.append(Card("Relic", 5))
            deck = Deck(excluded_cards)

        winner_list = []
        for player in player_list:
            # if there is a draw, players share the win
            if len(winner_list) == 0 or player.chest == winner_list[0].chest:
                winner_list.append(player)
            elif player.chest > winner_list[0].chest:
                winner_list = [player]

        return [player.player_id for player in winner_list]

    def start(self):
        winners = self.run_game()
        logging.info(str(winners) + " winner winner chicken dinner!")
        self.engine_interface.report_outcome(winners, self.match_history)


if __name__ == '__main__':
    game_engine = GameEngine()
    game_engine.start()
