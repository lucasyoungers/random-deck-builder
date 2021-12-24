#!/usr/bin/env python3

import math
import random
import os
import time
import json

import requests
from pokemontcgsdk import RestClient

from modules.get_from_api import *
from modules.card_printer import *
from modules.secret import API_KEY


"""
TODO:
- revamp add_trainers() such that it adds more intelligent card chocies
"""


class Deck:
    def __init__(self, seed_1: dict=None, seed_2: dict=None,
            format: str="unlimited") -> None:
        self.deck = []

        def __format_in(format: str) -> bool:
            return (seed_1 and seed_1["legalities"][format] == "Legal" or
                    seed_2 and seed_2["legalities"][format] == "Legal")

        # change legality of deck based on passed seed
        if not format and __format_in("unlimited"):
            format = "unlimited"
        elif not format and __format_in("expanded"):
            format = "expanded"
        elif format.lower() in ("standard", "expanded", "unlimited"):
            format = format.lower()

        # curate card pool based on format
        all_cards = []
        with open("api/cards.json", "r") as file:
            all_cards = json.load(file)
        self.cards = [card for card in all_cards
                if card["legalities"][format] == "Legal"]

        def __random_seed(seed, stage):
            if seed is None:
                seed = random.choice([card for card in self.cards
                        if card["subtypes"] and stage in card["subtypes"]])
            return seed

        self.seed_1 = __random_seed(seed_1, "Stage 2")
        self.seed_2 = __random_seed(seed_2, "Stage 1")

    def __add_seed(self, seed: dict) -> None:
        """Fill the deck with four cards based on a seed."""
        self.deck.append(seed)
        seeds = [card for card in self.cards
                if card["name"] == seed["name"]
                or card["evolvesFrom"] == seed["evolvesFrom"] != None]
        for _ in range(3):
            self.deck.append(random.choice(seeds))

    def __add_prevolutions(self) -> None:
        """
        Fill in prevolutions for each evolution in the deck.
        ONLY USE ONCE AFTER ALL SEEDS HAVE BEEN ADDED.
        """
        for evolution in self.deck:
            if evolution["evolvesFrom"]:
                seedlings = [card for card in self.cards
                        if card["name"] == evolution["evolvesFrom"]]
                if seedlings:
                    self.deck.append(random.choice(seedlings))

    def __add_trainers(self):
        """Fill the deck with pseudo-random trainers."""
        get_trainers = lambda subtype: [card for card in self.cards
                if card["subtypes"] and subtype in card["subtypes"]]

        supporters = get_trainers("Supporter")
        items = get_trainers("Item")
        stadiums = get_trainers("Stadium")

        for _ in range(8):
            self.deck.append(random.choice(supporters))
        
        for _ in range(16):
            self.deck.append(random.choice(items))

        for _ in range(4):
            self.deck.append(random.choice(stadiums))

    def __add_energy(self):
        """Fill the deck with appropriate Energy cards."""
        energy_in_deck = []
        for attacker in (card for card in self.deck if card["attacks"]):
            for attack in attacker["attacks"]:
                energy_in_deck.extend(attack["cost"])

        # how many of each energy type there should be
        types = {}
        for energy in (e for e in energy_in_deck if e != "Colorless"):
            types[energy] = types.get(energy, 0) + 1

        # sort types into a main and other types
        main_type = max(types, key=types.get)
        other_types = [e for e in types if e != main_type]

        # allocate rounded down energy count to each non-main type
        for energy in other_types:
            types[energy] = math.floor(types[energy]
                    * (60 - len(self.deck)) / sum(types.values()))
        
        # allocate the rest to the main type
        types[main_type] = (60 - len(self.deck)
                - sum([types[e] for e in other_types]))

        for energy in types:
            typed_energy = [card for card in self.cards
                    if card["supertype"] == "Energy"
                    and card["subtypes"] != None
                    and "Basic" in card["subtypes"]
                    and energy in card["name"]]
            for _ in range(types.get(energy)):
                if typed_energy:
                    self.deck.append(random.choice(typed_energy))

    def generate_deck(self) -> None:
        """Generate a deck given an optional seed and secondary seed."""
        self.__add_seed(self.seed_1)
        self.__add_seed(self.seed_2)
        self.__add_prevolutions()
        self.__add_trainers()
        self.__add_energy()

    def print(self) -> None:
        """Downloads the deck as a pdf to the current directory."""

        images = [card["images"]["large"] for card in self.deck]
        # print(images)
        # quit()
        name = self.seed_1["name"] + "_" + str(round(time.time() * 10000))
        print_pdf(images, name)

        # path_name = self.seed_1["name"] + "_" + str(round(time.time() * 10000))

        # # download the deck images to a folder
        # os.makedirs(path_name)
        # for card in self.deck:
        #     self.download(card["images"]["large"], path_name, card["name"])
        
        # # generate a pdf of the deck in the same folder
        # print_pdf(get_files(path_name), path_name)

        # # delete the card images after being downloaded
        # shutil.rmtree(path_name)

    # @staticmethod
    # def download(url: str, dirname: str, name: str) -> None:
    #     """Download a file from a url to the current directory."""
    #     r = requests.get(url)
    #     ext = url[url.rindex('.'):] # .png, .jpg, etc
    #     timestamp = round(time.time() * 10000)
    #     with open(f"{dirname}/{name}_{timestamp}{ext}", "wb") as file:
    #         file.write(r.content)

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
