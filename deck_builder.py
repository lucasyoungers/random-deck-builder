import random
import os
import shutil
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

    def __init__(self) -> None:
        self.deck = []

    def add_seed(self, seed: dict) -> None:
        """Fill the deck with four cards based on a seed."""
        self.deck.append(seed)
        seeds = [card for card in self.CARDS
                if card["name"] == seed["name"]
                or card["evolvesFrom"] == seed["evolvesFrom"] is not None]
        for _ in range(3):
            self.deck.append(random.choice(seeds))

    def add_prevolutions(self) -> None:
        """
        Fill in prevolutions for each evolution in the deck.
        ONLY USE ONCE AFTER ALL SEEDS HAVE BEEN ADDED.
        """
        for evolution in self.deck:
            if evolution["evolvesFrom"] is not None:
                seedlings = [card for card in self.CARDS
                        if card["name"] == evolution["evolvesFrom"]]
                self.deck.append(random.choice(seedlings))

    def generate_deck(self, seed: dict=None, secondary_seed: dict=None) -> None:
        """Generate a deck given an optional seed and secondary seed."""
        if seed is None:
            stage_2 = [card for card in self.CARDS
                    if card["subtypes"] is not None
                    and "Stage 2" in card["subtypes"]]
            seed = random.choice(stage_2)

        if secondary_seed is None:
            stage_1 = [card for card in self.CARDS
                    if card["types"] is not None
                    and self.seed["types"][0] in card["types"]
                    and card["subtypes"] is not None
                    and "Stage 1" in card["subtypes"]]
            secondary_seed = random.choice(stage_1)

        self.add_seed(seed)
        self.add_seed(secondary_seed)

    def print(self) -> None:
        """Downloads the deck as a pdf to the current directory."""

        path_name = self.seed["name"] + "_" + str(round(time.time() * 10000))

        # download the deck images to a folder
        os.makedirs(path_name)
        for card in self.deck:
            self.download(card["images"]["large"], path_name, card["name"])
        
        # generate a pdf of the deck in the same folder
        print_files(get_files(path_name), path_name)

        # delete the card images after being downloaded
        shutil.rmtree(path_name)

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
    deck.add_seed()
    deck.add_second_line()
    deck.add_prevolutions()
    deck.print()


if __name__ == "__main__":
    main()
