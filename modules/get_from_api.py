import json
from pokemontcgsdk import Card, Set, Type, Supertype, Subtype, Rarity, RestClient
from .secrets import API_KEY

RestClient.configure(API_KEY)

def get(json_file_name):
    with open(f"api/{json_file_name}.json", "w") as file:
        obj = None
        if json_file_name == "cards":
            obj = Card.all()
        elif json_file_name == "sets":
            obj = Set.all()
        elif json_file_name == "types":
            obj = Type.all()
        elif json_file_name == "supertypes":
            obj = Supertype.all()
        elif json_file_name == "subtypes":
            obj = Subtype.all()
        elif json_file_name == "rarities":
            obj = Rarity.all()
        
        data = json.dumps(obj, indent=4, default=lambda o: o.__dict__)
        file.write(str(data))

# takes 15 minutes
def get_cards():
    get("cards")

def get_sets():
    get("sets")

def get_types():
    get("types")

def get_supertypes():
    get("supertypes")

def get_subtypes():
    get("subtypes")

def get_rarities():
    get("rarities")

# takes 15 minutes
def get_all():
    for obj in ("cards", "sets", "types", "supertypes", "subtypes", "rarities"):
        get(obj)