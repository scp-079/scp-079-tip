# SCP-079-TIP - Here's a tip
# Copyright (C) 2019-2020 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-TIP.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pickle
from os import listdir, mkdir, remove
from os.path import exists, isfile, join
from random import choice
from shutil import move, rmtree
from string import ascii_letters, digits


def delete_file(path: str) -> bool:
    # Delete a file
    result = False

    try:
        if not(path and exists(path)):
            return False

        result = remove(path) or True
    except Exception as e:
        print(f"Delete file error: {e}")

    return result


def get_keywords(text: str) -> dict:
    # Get keywords
    result = {}
    # result = {
    #     "keyword1 || keyword2": "reply_text"
    # }

    try:
        # Check the text
        if not text:
            return {}

        text_list = [t for t in text.split("\n+++") if t]

        if not text_list or len(text_list) % 2 != 0:
            return {}

        # Get keyword_list
        keyword_list = [t.strip() for t in text_list[0::2]]
        reply_list = [t.strip() for t in text_list[1::2]]

        # Get keyword dict
        result = {}

        for i in range(len(keyword_list)):
            keyword = keyword_list[i]
            reply = reply_list[i]
            result[keyword] = reply
    except Exception as e:
        print(f"Get keywords error: {e}")

    return result


def get_reply(the_type: str, config: dict, origin: str) -> str:
    # Get reply text
    result = ""

    try:
        if not origin or not origin.strip():
            return origin.strip()

        text = config.get(f"{the_type}_button")
        link = config.get(f"{the_type}_link")

        if not text or not link:
            return origin

        text_list = [u.strip() for u in text.split("||") if u.strip()]
        link_list = [u.strip() for u in link.split("||") if u.strip()]

        if len(text_list) != len(link_list) or len(text_list) > 6:
            return origin

        result = origin + "\n++++++\n"

        for i in range(len(text_list)):
            result += f"{text_list[i]} || {link_list[i]}\n"

        result = result.strip()
    except Exception as e:
        print(f"Get reply error: {e}")

    return result


def move_file(src: str, dst: str) -> bool:
    # Move a file
    result = False

    try:
        if not src or not exists(src) or not dst:
            return False

        result = bool(move(src, dst))
    except Exception as e:
        print(f"Move file error: {e}")

    return result


def random_str(i: int) -> str:
    # Get a random string
    result = ""

    try:
        result = "".join(choice(ascii_letters + digits) for _ in range(i))
    except Exception as e:
        print(f"Random str error: {e}")

    return result


def remove_dir(path: str) -> bool:
    # Remove a directory
    result = False

    try:
        if not path or not exists(path):
            return False

        result = rmtree(path) or True
    except Exception as e:
        print(f"Remove dir error: {e}")

    return result


def files(path):
    # List files, not directories
    for file in listdir(path):
        if isfile(join(path, file)):
            yield file


def version_0() -> bool:
    # Version 0
    result = False

    try:
        exists("data/tmp") and rmtree("data/tmp")

        for path in ["data", "data/config", "data/pickle", "data/pickle/backup",
                     "data/log", "data/session", "data/tmp"]:
            not exists(path) and mkdir(path)

        result = True
    except Exception as e:
        print(f"Version 0 error: {e}")

    return result


def version_0_1_9() -> bool:
    # Version 0.1.9
    result = False

    try:
        if exists("data/pickle/current"):
            return False

        move_file("config.ini", "data/config/config.ini")
        move_file("start.txt", "data/config/start.txt")
        move_file("log", "data/log/log")

        for file in files("data"):
            if file.startswith("."):
                file = file[1:]
                move_file(f"data/.{file}", f"data/pickle/backup/{file}")
            else:
                move_file(f"data/{file}", f"data/pickle/{file}")

        move_file("bot.session", "data/session/bot.session")
        remove_dir("tmp")

        result = True
    except Exception as e:
        print(f"Version 0.1.9 error: {e}")

    return result


def version_0_2_0() -> bool:
    # Version 0.2.0
    result = False

    try:
        if exists("data/pickle/current"):
            with open("data/pickle/current", "rb") as f:
                current = pickle.load(f)

            if current >= "0.2.0":
                return False

        if not exists("data/pickle/configs"):
            return False

        with open("data/pickle/configs", "rb") as f:
            configs = pickle.load(f)

        # Create channels data
        channels = {}

        for gid in list(configs):
            channels[gid] = {}
            channels[gid]["aid"] = 0
            channels[gid]["id"] = configs[gid].get("channel")
            channels[gid]["text"] = configs[gid].get("channel_text")
            channels[gid]["button"] = configs[gid].get("channel_button")
            channels[gid]["link"] = configs[gid].get("channel_link")
            configs[gid]["channel"] = bool(configs[gid].get("channel"))
            configs[gid].pop("channel_text", None)
            configs[gid].pop("channel_button", None)
            configs[gid].pop("channel_link", None)

        with open("data/pickle/channels", "wb") as f:
            pickle.dump(channels, f)

        with open("data/pickle/configs", "wb") as f:
            pickle.dump(configs, f)

        # Create pinned_ids
        pinned_ids = {}

        for gid in list(configs):
            pinned_ids[gid] = 0

            if configs[gid].get("hold") and isinstance(int, configs[gid]["hold"]):
                pinned_ids[gid] = configs[gid]["hold"]
                configs[gid]["hold"] = True
            elif not isinstance(bool, configs[gid]["hold"]):
                configs[gid]["hold"] = False

        with open("data/pickle/pinned_ids", "wb") as f:
            pickle.dump(pinned_ids, f)

        with open("data/pickle/configs", "wb") as f:
            pickle.dump(configs, f)

        # Create keywords data
        keywords = {}

        for gid in list(configs):
            keywords[gid] = {}
            old_keywords = get_keywords(configs[gid].get("keyword_text", ""))

            if not old_keywords:
                continue

            for old_keyword in old_keywords:
                key = random_str(8)

                while keywords[gid].get(key):
                    key = random_str(8)

                keywords[gid][key] = {}
                keywords[gid][key]["words"] = {o.strip() for o in old_keyword.split("||")}
                keywords[gid][key]["words"].discard("")
                origin = old_keywords[old_keyword]
                keywords[gid][key]["reply"] = get_reply("keyword", configs[gid], origin)
                keywords[gid][key]["modes"] = {"include"}
                keywords[gid][key]["actions"] = {"reply"}
                keywords[gid][key]["target"] = "all"
                keywords[gid][key]["time"] = 300
                keywords[gid][key]["raw"] = f"{old_keyword}\n+++\n{keywords[gid][key]['reply']}"
                keywords[gid][key]["count"] = 0
                keywords[gid][key]["today"] = 0

            configs[gid].pop("keyword_text", None)
            configs[gid].pop("keyword_button", None)
            configs[gid].pop("keyword_link", None)

        with open("data/pickle/keywords", "wb") as f:
            pickle.dump(keywords, f)

        with open("data/pickle/configs", "wb") as f:
            pickle.dump(configs, f)

        # Create ots data

        # Create rms data

        # Create welcomes data

        print("Version 0.2.0 updated!")

        result = True
    except Exception as e:
        print(f"Version 0.2.0 error: {e}")

    return result


def version_control() -> bool:
    # Version control
    result = False

    try:
        version_0()

        version_0_1_9()

        version_0_2_0()

        result = True
    except Exception as e:
        print(f"Version control error: {e}")

    return result
