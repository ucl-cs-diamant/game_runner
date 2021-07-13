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


def main():
    fake_deck = Deck()
    print(fake_deck)


if __name__ == '__main__':
    main()