import random


def generate_deck():
    card_deck = []
    for i in range(5):
        card_deck.append(Card("Relic", 5))   # add 5 relic cards
    for i in range(3):
        card_deck.append(Card("Trap", "Spider"))    # 3 of each trap card
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

    return card_deck


class Card:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        return str(self.type + " " + self.value)


class Deck:
    def __init__(self):     # generate a full deck and shuffle it
        self.cards = generate_deck()
        self.shuffle_deck()

    def __str__(self):
        return str([(cardname.type + " " + str(cardname.value)) for cardname in self.cards])        # iterate over all cards and make a list of names and values

    def shuffle_deck(self):
        random.shuffle(self.cards)

    def pick_card(self):        # pick a card from the first element and remove it from the deck
        picked_card = self.cards[0]
        self.cards.pop(0)
        return picked_card


class Player:
    def __init__(self, playerID):
        self.playerID = playerID
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

    def decide_action(self):        # dummy roll 50/50 on leave/stay function
        decision = random.randint(0, 1)
        if decision == 0:        # if 0 is rolled, leave the cave
            self.continuing = False
        else:
            self.continuing = True


class Board:
    def __init__(self):
        self.route = []
        self.double_trap = False
        self.triggered_doubles = []
        self.relics_picked = 0       # note: relics are only counted when actually collected by an explorer on the way out

    def __str__(self):
        return str(self.route)

    def add_card(self, card):       # pick a card, if its another trap card, set double_trap to the trap card and kill the players at some point
        if card.type == "Trap":
            for board_card in self.route:
                if card.value == board_card.value:
                    self.double_trap = True
                    self.triggered_doubles.append(card.value)
                    break
        self.route.append(card)

    def reset_path(self):      # intentionally left out triggered doubles so it carries between paths
        self.route = []
        self.double_trap = None


def setup_game():
    initial_deck = Deck()
    new_player_list = []
    for i in range(5):
        new_player_list.append(Player(i))
    empty_board = Board()
    return initial_deck, new_player_list, empty_board


def single_turn(path_deck, path_player_list, path_board):

    # advancement phase
    path_board.add_card(path_deck.pick_card())
    active_players = len([player for player in path_player_list if player.in_cave])
    if active_players == 0:
        return True     # return immediately to move to the next expedition
    if path_board.route[-1].type == "Treasure":
        obtained_loot = int(path_board.route[-1].value / active_players)  # do integer division of the loot
        path_board.route[-1].value = path_board.route[-1].value % active_players  # set new value to reflect taken loot
        for player in path_player_list:       # go through the  player list and give all the players in the cave their loot
            if player.in_cave:
                player.pickup_loot(obtained_loot)

    if path_board.route[-1].type == "Relic":  # nothing extra is done when a relic is pulled
        pass

    if path_board.route[-1].type == "Trap":
        if path_board.double_trap:  # if its the second trap, kill all active players
            for player in path_player_list:  # go through the  player list and give all the players in the cave
                if player.in_cave:
                    player.kill_player()
            return True     # return a true flag to show the expedition should fail

    # decision phase

    for player in path_player_list:
        if player.in_cave:
            player.decide_action()

    leaving_players = len([player for player in path_player_list if player.in_cave and not player.continuing])  # number of players leaving

    # split the loot evenly between all leaving players, if one player is leaving, collect the relics

    if leaving_players > 0:
        for board_card in path_board.route:
            if board_card.type == "Treasure":       # split loot evenly between players on treasure cards
                obtained_loot = int(board_card.value / leaving_players)
                board_card.value = board_card.value % leaving_players

                for player in path_player_list:
                    if player.in_cave and not player.continuing:
                        player.pickup_loot(obtained_loot)

            if board_card.type == "Relic":
                if leaving_players == 1 and board_card.value != 0:
                    for player in path_player_list:     # find the leaving player
                        if player.in_cave and not player.continuing:
                            if path_board.relics_picked >= 3:        # increase the worth of a relic if its the last 2 from 5 to 10
                                player.pickup_loot(board_card.value * 2)
                            else:
                                player.pickup_loot(board_card.value)
                            path_board.relics_picked += 1
                            board_card.value = 0

            if board_card.type == "Trap":       # dont care about traps
                pass

    # once the board calcs are done, the players need to actually leave the cave
    for player in path_player_list:
        if player.in_cave and not player.continuing:
            player.leave_cave()

    return False    # return a false to keep the expedition going


def main():
    deck, player_list, board = setup_game()
    deck.cards[0] = Card("Relic", 5)
    deck.cards[1] = Card("Trap", "Snake")
    deck.cards[2] = Card("Treasure", 15)
    deck.cards[3] = Card("Relic", 5)
    deck.cards[4] = Card("Relic", 5)
    deck.cards[5] = Card("Relic", 5)
    deck.cards[6] = Card("Trap", "Snake")
    single_turn(deck, player_list, board)
    success = single_turn(deck, player_list, board)
    success = single_turn(deck, player_list, board)
    success = single_turn(deck, player_list, board)
    success = single_turn(deck, player_list, board)
    success = single_turn(deck, player_list, board)
    player_list[4].in_cave = True
    player_list[4].pocket = 100
    success = single_turn(deck, player_list, board)
    print(success)


if __name__ == '__main__':
    main()