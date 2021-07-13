import random


def generate_deck():
    card_deck = []
    for i in range(5):
        card_deck.append("Relic")   # add 5 relic cards
    for i in range(3):
        card_deck.append("Spider Trap")  # 3 of each trap card
        card_deck.append("Snake Trap")
        card_deck.append("Lava Trap")
        card_deck.append("Boulder Trap")
        card_deck.append("Ram Trap")
    for i in range(1,16):
        card_deck.append(i) # add 15 treasure cards
    return card_deck


class Deck:
    def __init__(self):     # generate a full deck and shuffle it
        self.cards = generate_deck()
        self.shuffle_deck()

    def __str__(self):
        return str(self.cards)

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
        self.in_cave = False    # whether a player is currently in the cave
        self.continuing = False     # the players decision to continue

    def leave_cave(self):       # player leaves cave safely and stores their loot
        self.in_cave = False
        self.continuing = False
        self.chest += self.pocket
        self.pocket = 0

    def kill_player(self):      # player dies in the cave, loot is lost
        self.pocket = 0
        self.in_cave = False
        self.continuing = False

    def pickup_loot(self, amount):      # player picks up some loot
        self.pocket += amount


def main():
    fake_deck = Deck()
    print(fake_deck)


if __name__ == '__main__':
    main()