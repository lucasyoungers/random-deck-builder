import random
import os
import time
import json

import requests
from pokemontcgsdk import RestClient

from modules.get_from_api import *
from modules.card_printer import *
from modules.secrets import API_KEY


class Deck:
    CARDS = [] # reference to full card database
    with open("api/cards.json", "r") as file:
        CARDS = json.load(file)

    def __init__(self, *, seed: dict=None) -> None:
        stage_2 = [card for card in self.CARDS if card["subtypes"] is not None
                and "Stage 2" in card["subtypes"]]
        self.seed = seed or random.choice(stage_2)
        self.deck = []

    def add_seed_line(self) -> None:
        # add "seeds" (evolutions)
        self.deck.append(self.seed)
        seeds = [card for card in self.CARDS
                if card["name"] == self.seed["name"]
                or card["evolvesFrom"] == self.seed["evolvesFrom"] is not None]
        for _ in range(3):
            self.deck.append(random.choice(seeds))

        # add "seedlings" (prevolutions)
        for evolution in self.deck:
            if evolution["evolvesFrom"] is not None:
                seedlings = [card for card in self.CARDS
                        if card["name"] == evolution["evolvesFrom"]]
                self.deck.append(random.choice(seedlings))

    def print(self) -> None:
        path_name = self.seed["name"] + "_" + str(round(time.time() * 10000))

        # download the deck images to a folder
        os.makedirs(path_name)
        for card in self.deck:
            self.download(card["images"]["large"], path_name, card["name"])
        
        # generate a pdf of the deck in the same folder
        print_files(get_files(path_name), path_name)

    @staticmethod
    def download(url: str, dirname: str, name: str) -> None:
        """Download a file from a url to the current directory."""
        r = requests.get(url)
        ext = url[url.rindex('.'):] # .png, .jpg, etc
        timestamp = round(time.time() * 10000)
        with open(f"{dirname}/{name}_{timestamp}{ext}", "wb") as file:
            file.write(r.content)

    def __str__(self) -> str:
        return str([card["name"] + "_" + card["id"] for card in self.deck])


def main() -> None:
    RestClient.configure(API_KEY)

    # refresh api if enough time has passed
    if (time.time() - os.path.getmtime("api/cards.json")) / 3600 > 24:
        get_all()

    deck = Deck()
    deck.add_seed_line()
    deck.print()


if __name__ == "__main__":
    main()
