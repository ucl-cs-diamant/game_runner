import numpy as np


def generate_deck(exclusions: list) -> list:
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
        return str(self.card_type + " " + self.value)


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

    def decide_action(self):        # dummy roll 50/50 on leave/stay function
        self._dispatch_action_request()  # todo: to implement

        decision = np.random.randint(0, 2)
        if decision:        # if 0 is rolled, leave the cave
            self.continuing = True
            return
        self.continuing = False


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
    new_player_list = []
    for i in range(6):
        new_player_list.append(Player(i))
    empty_board = Board()
    return initial_deck, new_player_list, empty_board


def advancement_phase(path_deck, path_player_list, path_board):
    path_board.add_card(path_deck.pick_card())
    active_players = len([player for player in path_player_list if player.in_cave])
    if active_players == 0:
        return True  # return immediately to move to the next expedition

    # Not actually sure if python is able to do inline extraction of these list accesses
    last_route = path_board.route[-1]  # todo: rename this, no clue if that's what this means

    if last_route.card_type == "Treasure":
        obtained_loot = last_route.value // active_players  # do integer division of the loot
        last_route.value = last_route.value % active_players  # set new value to reflect taken loot
        for player in path_player_list:  # go through the player list and give all the players in the cave their loot
            if player.in_cave:
                player.pickup_loot(obtained_loot)

    if last_route.card_type == "Relic":  # nothing extra is done when a relic is pulled
        pass  # <-----------------  did you mean continue? or can this `if` be removed altogether?

    if last_route.card_type == "Trap":
        if path_board.double_trap:  # if its the second trap, kill all active players
            for player in path_player_list:  # go through the  player list and give all the players in the cave
                if player.in_cave:
                    player.kill_player()
            return True  # return a true flag to show the expedition should fail
    else:
        return False


def decision_phase(path_player_list, path_board):
    for player in path_player_list:
        if player.in_cave:
            player.decide_action()  # todo: replace with

    # number of players leaving
    leaving_players = len([player for player in path_player_list if player.in_cave and not player.continuing])

    # split the loot evenly between all leaving players, if one player is leaving, collect the relics

    if leaving_players > 0:
        for board_card in path_board.route:
            if board_card.card_type == "Treasure":       # split loot evenly between players on treasure cards
                obtained_loot = int(board_card.value / leaving_players)
                board_card.value = board_card.value % leaving_players

                for player in path_player_list:
                    if player.in_cave and not player.continuing:
                        player.pickup_loot(obtained_loot)

            if board_card.card_type == "Relic":
                if leaving_players == 1 and board_card.value != 0:
                    for player in path_player_list:     # find the leaving player
                        if player.in_cave and not player.continuing:
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
    for player in path_player_list:
        if player.in_cave and not player.continuing:
            player.leave_cave()


def single_turn(path_deck, path_player_list, path_board):
    # advancement phase
    expedition_failed = advancement_phase(path_deck, path_player_list, path_board)
    if expedition_failed:   # propagate the failure up
        return True
    # decision phase
    decision_phase(path_player_list, path_board)
    return False


def run_path(deck, player_list, board):     # runs through a path until all players leave or the run dies
    path_complete = False
    while not path_complete:
        path_complete = single_turn(deck, player_list, board)
    board.reset_path()      # reset board for a new path


def run_game():     # run a full game of diamant
    deck, player_list, board = setup_game()
    for path_num in range(5):      # do 5 paths
        run_path(deck, player_list, board)
        excluded_cards = board.triggered_doubles
        for relic_count in range(board.relics_picked):        # add an exclusion for every picked relic
            excluded_cards.append(Card("Relic", 5))
        deck = Deck(excluded_cards)

    winner = Player(-1)     # dummy player value
    for player in player_list:
        if player.chest > winner.chest:
            winner = player
    return winner.player_id


def debug_run(deck, player_list, board):        # debug command to do a failed run
    deck.cards[0] = Card("Relic", 5)
    deck.cards[1] = Card("Trap", "Snake")
    deck.cards[2] = Card("Treasure", 15)
    deck.cards[3] = Card("Relic", 5)
    deck.cards[4] = Card("Relic", 5)
    deck.cards[5] = Card("Relic", 5)
    deck.cards[6] = Card("Trap", "Snake")
    single_turn(deck, player_list, board)
    single_turn(deck, player_list, board)
    single_turn(deck, player_list, board)
    single_turn(deck, player_list, board)
    single_turn(deck, player_list, board)
    single_turn(deck, player_list, board)
    player_list[4].in_cave = True
    player_list[4].pocket = 100
    success = single_turn(deck, player_list, board)
    print(success)


def main():
    print(str(run_game()) + " winner winner chicken dinner!")


if __name__ == '__main__':
    main()
