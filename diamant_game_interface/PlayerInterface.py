from collections.abc import Callable


class PlayerInterface:
    def __init__(self, decision_callback: Callable):
        self.callback = None
        if callable(decision_callback):
            self.callback = decision_callback
            return
        raise ValueError("Decision callback not callable, expected callable callback")
