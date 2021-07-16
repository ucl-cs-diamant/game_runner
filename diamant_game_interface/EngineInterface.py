# from collections.abc import Callable
import requests
import time
import concurrent.futures
import tempfile
import tarfile


# todo: deal with http/https later
# noinspection HttpUrlsUsage
class EngineInterface:
    def __init__(self, server_address, server_port=80, ready_callback=None):
        self.players = []
        self.players_code_directories = {}
        self.player_processes = {}
        self.game_id = None
        self.server_address = server_address
        self.server_port = server_port
        self.ready = False
        # self.ready_callback = ready_callback

    # def set_ready_callback(self, ready_callback: Callable):
    #     assert callable(ready_callback)
    #     self.ready_callback = ready_callback

    def __fetch_match_data(self):
        while True:  # PEP315
            try:
                res = requests.get(f"http://{self.server_address}:{self.server_port}/requestMatch")
            except requests.ConnectionError:
                raise ValueError(f"{self.server_address}:{self.server_port} is not a valid address")
            if res.status_code == 200:
                break
            time.sleep(0.2)
        match_data = res.json()
        self.players = match_data["players"]  # todo: check against the actual API. I don't remember what it's like
        self.game_id = match_data["game_id"]

    def __fetch_player_code(self, player_id):
        # self.players_code_directories[player_id] = ''
        url = f"http://{self.server_address}:{self.server_port}/users/{player_id}/latest_code/"
        with requests.get(url) as res:
            res.raise_for_status()
            if res.status_code == 200:
                player_code_dir = tempfile.TemporaryDirectory()
                with tempfile.TemporaryFile() as tf:
                    tf.write(res.content)
                    tar = tarfile.open(fileobj=tf)
                    tar.extractall(path=player_code_dir.name)
                self.players_code_directories[player_id] = player_code_dir
                return
            raise requests.exceptions.RequestException

    def __prepare_player_code(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            fetch_player_code_futures = [executor.submit(self.__fetch_player_code, player_id)
                                         for player_id in self.players]
            # concurrent.futures.wait(fetch_player_code_futures)
            for future in concurrent.futures.as_completed(fetch_player_code_futures):
                if future.exception() is not None:
                    return False
        return True

    def __launch_players(self):
        pass

    def init_game(self):
        self.__fetch_match_data()
        if not self.__prepare_player_code():
            pass
            # handle game abortion
        self.__launch_players()
        self.ready = True
        # if self.ready_callback is not None:
        #     self.ready_callback()
