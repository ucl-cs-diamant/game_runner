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
    def __init__(self, player_id):
        self.player_id = player_id
        self.chest = 0
        self.pocket = 0     # how much a player has on hand mid exploration
        self.in_cave = True    # whether a player is currently in the cave
        self.continuing = True     # the players decision to continue

    def leave_cave(self):       # player leaves cave safely and stores their loot
        self.in_cave = False
        self.continuing = False
        self.chest += self.pocket
        self.pocket = 0

    def kill_player(self):      # player dies in the cave, loot is lost, and values reset to normal
        self.pocket = 0
        self.in_cave = False
        self.continuing = False

    def pickup_loot(self, amount):      # player picks up some loot
        self.pocket += amount

    def _dispatch_action_request(self):  # todo: to implement
        pass

    # def decide_action(self, ei):        # dummy roll 50/50 on leave/stay function
    #
    #     decision = np.random.randint(0, 2)
    #     if decision:        # if 0 is rolled leave
    #         self.continuing = True
    #         return
    #     self.continuing = False


class Board:
    def __init__(self):
        self.route = []
        self.double_trap = False
        self.triggered_doubles = []
        self.relics_picked = 0  # note: relics are only counted when actually collected by an explorer on the way out

    def __str__(self):
        return str(self.route)

    # pick a card, if its another trap card, set double_trap to the trap card and kill the players at some point
    def add_card(self, card):
        if card.card_type == "Trap":
            for board_card in self.route:
                if card.value == board_card.value:
                    self.double_trap = True
                    self.triggered_doubles.append(card)
                    break
        self.route.append(card)

    def reset_path(self):  # intentionally left out triggered doubles so it carries between paths
        self.route = []
        self.double_trap = None


def setup_game():
    initial_deck = Deck()
    empty_board = Board()
    return initial_deck, empty_board


def handle_treasure_loot(board_card, players):
    # board_card is either the new card, or the card on the route as the players are leaving 
    # players are the players who decided to leave or the remaining active players
    
    no_players = len(players);
    obtained_loot = board_card.value // no_players # do integer division of the loot
    board_card.value = board_card.value % no_players # set new value to reflect taken loot

    for player in players: # go through the provided player list and give them the divided loot
        player.pickup_loot(obtained_loot)


def advancement_phase(path_deck, path_player_list, path_board):
    path_board.add_card(path_deck.pick_card())

    active_players = [player for player in path_player_list if player.in_cave]
    no_active_players = len(active_players)
    if no_active_players == 0:
        return True  # return immediately to move to the next expedition

    # Not actually sure if python is able to do inline extraction of these list accesses
    last_route = path_board.route[-1]

    if last_route.card_type == "Treasure":
        handle_treasure_loot(last_route, active_players)

    if last_route.card_type == "Relic":  # nothing extra is done when a relic is pulled
        pass  # <-----------------  did you mean continue? or can this `if` be removed altogether?

    if last_route.card_type == "Trap":
        if path_board.double_trap:  # if its the second trap, kill all active players
            for player in active_players:  # go through the  player list and kill all the remaining active players in the cave
                player.kill_player()
            return True  # return a true flag to show the expedition should fail
    else:
        return False

async def decision_phase(path_player_list, path_board, ei):
    # for player in path_player_list:
    #     if player.in_cave:
    #         player.decide_action()
    player_decisions = await ei.request_decisions()
    for player_decision in player_decisions:
        path_player_list[player_decision["player_id"]].continuing = player_decision["decision"]


    # leaving players leaving and number of leaving players
    leaving_players = [player for player in path_player_list if player.in_cave and not player.continuing] 
    no_leaving_players = len(leaving_players)

    # split the loot evenly between all leaving players, if one player is leaving, collect the relics

    if no_leaving_players > 0:
        for board_card in path_board.route:
            if board_card.card_type == "Treasure":       # split loot evenly between players on treasure cards
                handle_treasure_loot(board_card, leaving_players)

            if board_card.card_type == "Relic":
                if no_leaving_players == 1 and board_card.value != 0: # <-- do we need to check that board_card.value != 0? Aren't relic always worth more than 0 even when the Card object is created?
                    for player in leaving_players:
                            # increase the worth of a relic if its the last 2 from 5 to 10
                            if path_board.relics_picked >= 3:
                                player.pickup_loot(board_card.value * 2)
                            else:
                                player.pickup_loot(board_card.value)
                            path_board.relics_picked += 1
                            board_card.value = 0

            if board_card.card_type == "Trap":       # dont care about traps
                pass

    # once the board calculations are done, the players need to actually leave the cave
    for player in leaving_players:
            player.leave_cave()


async def single_turn(path_deck, path_player_list, path_board, ei):
    # advancement phase
    expedition_failed = advancement_phase(path_deck, path_player_list, path_board)
    if expedition_failed:   # propagate the failure up
        return True
    # decision phase
    await decision_phase(path_player_list, path_board, ei)
    return False


async def run_path(deck, player_list, board, ei):     # runs through a path until all players leave or the run dies
    path_complete = False
    while not path_complete:
        path_complete = await single_turn(deck, player_list, board, ei)
    board.reset_path()      # reset board for a new path


async def run_game(engine_interface):     # run a full game of diamant
    deck, board = setup_game()
    player_list = [Player(player_id) for player_id in engine_interface.players]
    for path_num in range(5):      # do 5 paths
        await run_path(deck, player_list, board, engine_interface)
        excluded_cards = board.triggered_doubles
        for relic_count in range(board.relics_picked):        # add an exclusion for every picked relic
            excluded_cards.append(Card("Relic", 5))
        deck = Deck(excluded_cards)

    winner_list = []
    for player in player_list:
        if len(winner_list) == 0 or player.chest == winner_list[0].chest:  # if there is a draw, players share the win
            winner_list.append(player)
        elif player.chest > winner_list[0].chest:
            winner_list = [player]

    return [player.player_id for player in winner_list]


# def debug_run(deck, player_list, board):        # debug command to do a failed run
#     deck.cards[0] = Card("Relic", 5)
#     deck.cards[1] = Card("Trap", "Snake")
#     deck.cards[2] = Card("Treasure", 15)
#     deck.cards[3] = Card("Relic", 5)
#     deck.cards[4] = Card("Relic", 5)
#     deck.cards[5] = Card("Relic", 5)
#     deck.cards[6] = Card("Trap", "Snake")
#     single_turn(deck, player_list, board)
#     single_turn(deck, player_list, board)
#     single_turn(deck, player_list, board)
#     single_turn(deck, player_list, board)
#     single_turn(deck, player_list, board)
#     single_turn(deck, player_list, board)
#     player_list[4].in_cave = True
#     player_list[4].pocket = 100
#     success = single_turn(deck, player_list, board)
#     print(success)


async def main():
    engine_interface = EngineInterface('localhost')  # todo: replace with environment variables
    await engine_interface.init_game()
    print(str(await run_game(engine_interface)) + " winner winner chicken dinner!")


if __name__ == '__main__':
    asyncio.run(main())
