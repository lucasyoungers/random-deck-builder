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
    def __init__(self, seed_1: dict=None, seed_2: dict=None,
            format: str="unlimited") -> None:
        self.deck = []

        # change legality of deck based on passed seed
        if not format and ((seed_1 is not None
                and seed_1["legalities"]["unlimited"] == "Legal")
                or (seed_2 is not None
                and seed_2["legalities"]["unlimited"] == "Legal")):
            format = "unlimited"
        elif not format and ((seed_1 is not None
                and seed_1["legalities"]["expanded"] == "Legal")
                or (seed_2 is not None
                and seed_2["legalities"]["expanded"] == "Legal")):
            format = "expanded"
        else:
            format = format.lower()

        # curate card pool based on format
        all_cards = []
        with open("api/cards.json", "r") as file:
            all_cards = json.load(file)
        self.cards = [card for card in all_cards
                if card["legalities"][format] == "Legal"]

        # randomly generate a main seed if necessary
        if seed_1 is None:
            stage_2 = [card for card in self.cards
                    if card["subtypes"] is not None
                    and "Stage 2" in card["subtypes"]]
            seed_1 = random.choice(stage_2)
        self.seed_1 = seed_1

        # randomly generate a secondary seed if necessary
        if seed_2 is None:
            stage_1 = [card for card in self.cards
                    if card["types"] is not None
                    and self.seed_1["types"][0] in card["types"]
                    and card["subtypes"] is not None
                    and "Stage 1" in card["subtypes"]]
            seed_2 = random.choice(stage_1)
        self.seed_2 = seed_2

    def add_seed(self, seed: dict) -> None:
        """Fill the deck with four cards based on a seed."""
        self.deck.append(seed)
        seeds = [card for card in self.cards
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
                seedlings = [card for card in self.cards
                        if card["name"] == evolution["evolvesFrom"]]
                self.deck.append(random.choice(seedlings))

    def add_trainers(self):
        """Fill the deck with pseudo-random trainers."""
        get_trainers = lambda subtype: [card for card in self.cards
                if card["subtypes"] is not None
                and subtype in card["subtypes"]]

        supporters = get_trainers("Supporter")
        items = get_trainers("Item")
        stadiums = get_trainers("Stadium")

        for _ in range(8):
            self.deck.append(random.choice(supporters))
        
        for _ in range(16):
            self.deck.append(random.choice(items))

        for _ in range(4):
            self.deck.append(random.choice(stadiums))

    def add_energy(self):
        """Fill the deck with appropriate Energy cards."""
        # supertype == Energy, subtype == Basic
        energies = [card for card in self.cards
                if card["supertype"] == "Energy"
                and card["subtypes"] is not None
                and "Basic" in card["subtypes"]
                and self.seed_1["types"][0] in card["name"]]
        energy = random.choice(energies)
        for _ in range(12):
            self.deck.append(energy)

    def generate_deck(self) -> None:
        """Generate a deck given an optional seed and secondary seed."""
        self.add_seed(self.seed_1)
        self.add_seed(self.seed_2)
        self.add_prevolutions()
        self.add_trainers()
        self.add_energy()

    def print(self) -> None:
        """Downloads the deck as a pdf to the current directory."""

        path_name = self.seed_1["name"] + "_" + str(round(time.time() * 10000))

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
    deck.generate_deck()
    deck.print()


if __name__ == "__main__":
    main()
