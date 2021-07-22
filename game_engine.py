import os

import numpy as np
import asyncio
from diamant_game_interface import EngineInterface
from typing import Union


def generate_deck(exclusions: Union[list, None]) -> list:
    card_deck = []
    for i in range(5):
        card_deck.append(Card("Relic", 5))  # add 5 relic cards
    for i in range(3):
        card_deck.append(Card("Trap", "Spider"))  # 3 of each trap card
        card_deck.append(Card("Trap", "Snake"))
        card_deck.append(Card("Trap", "Lava"))
        card_deck.append(Card("Trap", "Boulder"))
        card_deck.append(Card("Trap", "Ram"))

    # add 15 treasure cards
    card_deck.append(Card("Treasure", 5))
    card_deck.append(Card("Treasure", 5))
    card_deck.append(Card("Treasure", 9))
    card_deck.append(Card("Treasure", 14))
    card_deck.append(Card("Treasure", 3))
    card_deck.append(Card("Treasure", 17))
    card_deck.append(Card("Treasure", 2))
    card_deck.append(Card("Treasure", 7))
    card_deck.append(Card("Treasure", 7))
    card_deck.append(Card("Treasure", 1))
    card_deck.append(Card("Treasure", 11))
    card_deck.append(Card("Treasure", 11))
    card_deck.append(Card("Treasure", 4))
    card_deck.append(Card("Treasure", 15))
    card_deck.append(Card("Treasure", 13))

    if exclusions is not None:
        for excluded_card in exclusions:
            for card in card_deck:
                if card.card_type == excluded_card.card_type and card.value == excluded_card.value:
                    card_deck.remove(card)
                    break  # find a matching card, remove it once, and immediately break

    return card_deck


# match history = [match_event]
# match_event = {event_type:item, content:{}}
class MatchEvent:
    def __init__(self, event_type, content: dict):
        self.match_event = {"event_type": event_type, "content": content}

    def __str__(self):
        return str(self.match_event)

    # player_pickup.keys() = [player_id, pocket, amount]
    # player_death.keys() = [player_id, pocket]
    # player_leaves.keys() = [player_id, pocket, chest]
    # NOTE: all player values are snapshots of before the event happens

    # board_add_card.keys() = [card_type, value]

    # board_change_card.keys() = [card_index, card_type, value]
    # NOTE: card_index = index of board.route where card is located

    # board_trap_trigger.keys() = [card_type, value]
    # new_path.keys() = [path_num]


class MatchHistory:
    def __init__(self):
        self.match_timeline = []

    def __str__(self):
        match_string = "["
        if len(match_string) > 0:
            match_string += str(self.match_timeline[0])
            if len(self.match_timeline) > 1:
                for item in range(1, len(self.match_timeline)):
                    match_string += ", "
                    match_string += str(item)
        match_string += "]"
        return match_string

    def add_event(self, event: MatchEvent):
        self.match_timeline.append(event)


class Card:
    def __init__(self, card_type, value):
        self.card_type = card_type
        self.value = value

    def __str__(self):
        return str(self.card_type + " " + str(self.value))


class Deck:
    def __init__(self, exclusions=None):     # generate a full deck and shuffle it
        self.cards = generate_deck(exclusions)
        self.shuffle_deck()

    def __str__(self):
        # iterate over all cards and make a list of names and values
        return str([(card_name.card_type + " " + str(card_name.value)) for card_name in self.cards])

    def shuffle_deck(self):
        # random.shuffle(self.cards)
        np.random.shuffle(self.cards)

    def pick_card(self):        # pick a card from the first element and remove it from the deck
        picked_card = self.cards[0]
        self.cards.pop(0)
        return picked_card


class Player:
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.chest = 0
        self.pocket = 0     # how much a player has on hand mid exploration
        self.in_cave = True    # whether a player is currently in the cave
        self.continuing = True     # the players decision to continue

    def leave_cave(self, match_history: MatchHistory):       # player leaves cave safely and stores their loot
        match_history.add_event(MatchEvent("player_leaves",
                                           {"player_id": self.player_id, "pocket": self.pocket, "chest": self.chest}))
        self.in_cave = False
        self.continuing = False
        self.chest += self.pocket
        self.pocket = 0

    def kill_player(self, match_history: MatchHistory):
        # player dies in the cave, loot is lost, and values reset to normal
        match_history.add_event(MatchEvent("player_death", {"player_id": self.player_id, "pocket": self.pocket}))
        self.pocket = 0
        self.in_cave = False
        self.continuing = False

    def pickup_loot(self, amount, match_history: MatchHistory):      # player picks up some loot
        match_history.add_event(MatchEvent("player_pickup", {"player_id": self.player_id, "pocket": self.pocket,
                                                             "amount": amount}))
        self.pocket += amount

    def _dispatch_action_request(self):  # todo: to implement
        pass

    def reset_player(self):     # reset a player for the next path
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
        if card.card_type == "Trap":    # Traps need to checked before being added for logic reasons
            for board_card in self.route:
                if card.value == board_card.value:
                    self.double_trap = True
                    match_history.add_event(MatchEvent("board_trap_trigger", {"card_type": card.card_type,
                                                                              "value": card.value}))
                    self.excluded_cards.append(card)
                    break

        self.route.append(card)

        if card.card_type == "Relic":   # Relics can be changed after adding neatly
            self.relics_picked += 1
            self.excluded_cards.append(card)
            if self.relics_picked > 3:  # 4th and 5th relic have 10 value
                self.route[-1].value = 10

        match_history.add_event(MatchEvent("board_add_card", {"card_type": card.card_type, "value": card.value}))

    def reset_path(self):  # intentionally left out triggered doubles so it carries between paths
        self.route = []
        self.double_trap = False


def setup_game():
    initial_deck = Deck()
    empty_board = Board()
    return initial_deck, empty_board


def handle_treasure_loot(board_card, card_index, players, match_history: MatchHistory):
    # board_card is either the new card, or the card on the route as the players are leaving
    # players are the players who decided to leave or the remaining active players
    no_players = len(players)
    obtained_loot = board_card.value // no_players  # do integer division of the loot
    board_card.value = board_card.value % no_players  # set new value to reflect taken loot
    match_history.add_event(MatchEvent("board_change_card", {"card_index": card_index,
                                                             "card_type": board_card.card_type,
                                                             "value": board_card.value}))

    for player in players:  # go through the provided player list and give them the divided loot
        player.pickup_loot(obtained_loot, match_history)


def advancement_phase(path_deck, path_player_list, path_board, match_history: MatchHistory):
    path_board.add_card(path_deck.pick_card(), match_history)

    active_players = [player for player in path_player_list if player.in_cave]
    no_active_players = len(active_players)
    if no_active_players == 0:
        return True  # return immediately to move to the next expedition

    last_route = path_board.route[-1]

    if last_route.card_type == "Treasure":
        handle_treasure_loot(last_route, path_board.route.index(last_route), active_players, match_history)

    if last_route.card_type == "Relic":  # this IF is here for sheer readability and does nothing
        pass

    if last_route.card_type == "Trap":
        if path_board.double_trap:  # if its the second trap, kill all active players
            for player in active_players:  # go through the  player list and kill all the remaining active players
                player.kill_player(match_history)
            return True  # return a true flag to show the expedition should fail
    else:
        return False


async def make_decisions(path_player_list, ei):   # actually make the players make a decision
    # for player in path_player_list:
    #     if player.in_cave:
    #         player.decide_action()
    player_decisions = await ei.request_decisions()
    # for player_id in player_decisions:
    #     path_player_list[player_id].continuing = player_decisions[player_id]["decision"]
    for player in path_player_list:
        player.continuing = player_decisions[player.player_id]["decision"]


def handle_leaving_players(no_leaving_players, leaving_players, path_board, match_history: MatchHistory):
    # function that handles card values and loot distribution upon leaving
    if no_leaving_players > 0:
        for board_card in path_board.route:
            if board_card.card_type == "Treasure":       # split loot evenly between players on treasure cards
                handle_treasure_loot(board_card, path_board.route.index(board_card), leaving_players, match_history)

            # check if there is a relic to pick up (arguably pointless but it saves running the extra code 9/10 times)
            if board_card.card_type == "Relic" and board_card.value != 0:
                if no_leaving_players == 1:
                    for player in leaving_players:
                        player.pickup_loot(board_card.value, match_history)
                        board_card.value = 0
                        match_history.add_event(
                            MatchEvent("board_change_card", {
                                "card_index": path_board.route.index(board_card),
                                "card_type": board_card.card_type,
                                "value": board_card.value}))

            if board_card.card_type == "Trap":       # dont care about traps
                pass


async def decision_phase(path_player_list, path_board, ei, match_history: MatchHistory):
    await make_decisions(path_player_list, ei)

    # leaving players leaving and number of leaving players
    leaving_players = [player for player in path_player_list if player.in_cave and not player.continuing]
    no_leaving_players = len(leaving_players)

    # split the loot evenly between all leaving players, if one player is leaving, collect the relics
    handle_leaving_players(no_leaving_players, leaving_players, path_board, match_history)

    # once the board calculations are done, the players need to actually leave the cave
    for player in leaving_players:
        player.leave_cave(match_history)


async def single_turn(path_deck, path_player_list, path_board, ei, match_history):
    # advancement phase
    expedition_failed = advancement_phase(path_deck, path_player_list, path_board, match_history)
    if expedition_failed:   # propagate the failure up
        return True
    # decision phase
    await decision_phase(path_player_list, path_board, ei, match_history)
    return False


async def run_path(deck, player_list, board, ei, match_history):
    # runs through a path until all players leave or the run dies
    path_complete = False
    while not path_complete:
        path_complete = await single_turn(deck, player_list, board, ei, match_history)
    board.reset_path()      # reset board for a new path
    for player in player_list:      # reset all players so they are able to participate in the next path
        player.reset_player()


async def run_game(engine_interface):     # run a full game of diamant
    deck, board = setup_game()
    player_list = [Player(player_id) for player_id in engine_interface.players]

    match_history = MatchHistory()

    for path_num in range(5):      # do 5 paths
        match_history.add_event(MatchEvent("new_path", {"path_num": path_num}))
        await run_path(deck, player_list, board, engine_interface, match_history)
        excluded_cards = board.excluded_cards
        for relic_count in range(board.relics_picked):        # add an exclusion for every picked relic
            excluded_cards.append(Card("Relic", 5))
        deck = Deck(excluded_cards)

    winner_list = []
    for player in player_list:
        if len(winner_list) == 0 or player.chest == winner_list[0].chest:  # if there is a draw, players share the win
            winner_list.append(player)
        elif player.chest > winner_list[0].chest:
            winner_list = [player]

    return [player.player_id for player in winner_list], match_history


async def main():
    engine_interface = EngineInterface(os.environ.get("GAMESERVER_HOST", "GAMESERVER_HOST_MISSING"),
                                       int(os.environ.get("GAMESERVER_PORT", 80)))

    await engine_interface.init_game()
    winners, match_history = await run_game(engine_interface)
    print(str(winners) + " winner winner chicken dinner!")
    engine_interface.report_outcome(winners)

if __name__ == '__main__':
    asyncio.run(main())
