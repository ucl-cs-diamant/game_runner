from diamant_game_interface import PlayerInterface
import random


def handle_decision(game_state: dict):  # entrypoint for all game decisions
    print(game_state)
    return random.randint(0, 1)


if __name__ == "__main__":
    game = PlayerInterface(handle_decision)

    # do some more setup if needed

    game.start()  # blocking call
