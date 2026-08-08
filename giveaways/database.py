import json
import os
from datetime import datetime
from pathlib import Path


DATA_FOLDER = Path(__file__).resolve().parents[1] / "data"
DATA_FILE = DATA_FOLDER / "giveaways.json"


def create_storage():
    os.makedirs(DATA_FOLDER, exist_ok=True)

    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump({}, file, indent=4, ensure_ascii=False)


def load_giveaways():
    create_storage()

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_giveaways(data):
    create_storage()

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


def create_giveaway(
        message_id: int,
        channel_id: int,
        guild_id: int,
        prize: str,
        end_time: str,
        creator: int
):

    giveaways = load_giveaways()

    giveaways[str(message_id)] = {
        "message_id": message_id,
        "channel_id": channel_id,
        "guild_id": guild_id,

        "prize": prize,

        "creator": creator,

        "end_time": end_time,

        "participants": [],

        "ended": False
    }

    save_giveaways(giveaways)


def get_giveaway(message_id: int):

    giveaways = load_giveaways()

    return giveaways.get(str(message_id))


def add_participant(
        message_id: int,
        user_id: int
):

    giveaways = load_giveaways()

    giveaway = giveaways.get(str(message_id))


    if not giveaway:
        return False


    if user_id in giveaway["participants"]:
        return False


    giveaway["participants"].append(user_id)

    save_giveaways(giveaways)

    return True



def remove_participant(
        message_id: int,
        user_id: int
):

    giveaways = load_giveaways()

    giveaway = giveaways.get(str(message_id))


    if not giveaway:
        return


    if user_id in giveaway["participants"]:
        giveaway["participants"].remove(user_id)


    save_giveaways(giveaways)



def get_participants(message_id: int):

    giveaway = get_giveaway(message_id)

    if not giveaway:
        return []

    return giveaway["participants"]



def finish_giveaway(message_id: int):

    giveaways = load_giveaways()

    giveaway = giveaways.get(str(message_id))

    if giveaway:
        giveaway["ended"] = True
        save_giveaways(giveaways)
