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

import logging
import pickle
from codecs import getdecoder
from configparser import RawConfigParser
from os.path import exists
from string import ascii_lowercase
from threading import Lock
from typing import Dict, List, Set, Tuple, Union

from pyrogram import emoji
from pyrogram.types import Chat, ChatMember
from yaml import safe_load

from .checker import check_all, raise_error
from .version import version_control

# Path variables
CONFIG_PATH = "data/config/config.ini"
CUSTOM_LANG_PATH = "data/config/custom.yml"
LOG_PATH = "data/log"
PICKLE_BACKUP_PATH = "data/pickle/backup"
PICKLE_PATH = "data/pickle"
JOIN_PATH = "data/config/join.txt"
SESSION_DIR_PATH = "data/session"
SESSION_PATH = "data/session/bot.session"
START_PATH = "data/config/start.txt"
TMP_PATH = "data/tmp"

# Version control
version_control()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARNING,
    filename=f"{LOG_PATH}/log",
    filemode="a"
)
logger = logging.getLogger(__name__)

# Read data from config.ini

# [flag]
broken: bool = True

# [basic]
bot_token: str = ""
prefix: List[str] = []
prefix_str: str = "/!"

# [bots]
avatar_id: int = 0
captcha_id: int = 0
clean_id: int = 0
index_id: int = 0
lang_id: int = 0
long_id: int = 0
noflood_id: int = 0
noporn_id: int = 0
nospam_id: int = 0
tip_id: int = 0
user_id: int = 0
warn_id: int = 0

# [channels]
compromise_channel_id: int = 0
critical_channel_id: int = 0
debug_channel_id: int = 0
exchange_channel_id: int = 0
hide_channel_id: int = 0
test_group_id: int = 0
tip_channel_id: int = 0

# [custom]
default_group_link: str = "https://t.me/SCP_079_DEBUG"
leave_button: str = "申请使用"
leave_link: str = "https://scp-079.org/ApplyForUse/"
leave_reason: str = "需要授权方可使用"
manual_link: str = "https://manuals.scp-079.org/bots/tip/"
project_link: str = "https://scp-079.org/tip/"
project_name: str = "SCP-079-TIP"

# [emoji]
emoji_ad_single: int = 15
emoji_ad_total: int = 30
emoji_many: int = 15
emoji_protect: [bytes, str] = "\\U0001F642"
emoji_wb_single: int = 10
emoji_wb_total: int = 15

# [encrypt]
key: Union[str, bytes] = ""
password: str = ""

# [language]
lang: str = "cmn-Hans"
normalize: Union[bool, str] = "True"

# [mode]
aio: Union[bool, str] = "False"
backup: Union[bool, str] = "False"

# [time]
date_reset: str = "1st mon"
time_channel: int = 0
time_keyword: int = 0
time_ot: int = 0
time_rm: int = 0
time_welcome: int = 0

try:
    not exists(CONFIG_PATH) and raise_error(f"{CONFIG_PATH} does not exists")
    config = RawConfigParser()
    config.read(CONFIG_PATH)

    # [basic]
    bot_token = config.get("basic", "bot_token", fallback=bot_token)
    prefix_str = config.get("basic", "prefix", fallback=prefix_str)
    prefix = [p for p in list(prefix_str) if p]

    # [bots]
    avatar_id = int(config.get("bots", "avatar_id", fallback=avatar_id))
    captcha_id = int(config.get("bots", "captcha_id", fallback=captcha_id))
    clean_id = int(config.get("bots", "clean_id", fallback=clean_id))
    index_id = int(config.get("bots", "index_id", fallback=index_id))
    lang_id = int(config.get("bots", "lang_id", fallback=lang_id))
    long_id = int(config.get("bots", "long_id", fallback=long_id))
    noflood_id = int(config.get("bots", "noflood_id", fallback=noflood_id))
    noporn_id = int(config.get("bots", "noporn_id", fallback=noporn_id))
    nospam_id = int(config.get("bots", "nospam_id", fallback=nospam_id))
    tip_id = int(config.get("bots", "tip_id", fallback=tip_id))
    user_id = int(config.get("bots", "user_id", fallback=user_id))
    warn_id = int(config.get("bots", "warn_id", fallback=warn_id))

    # [channels]
    compromise_channel_id = int(config.get("channels", "compromise_channel_id", fallback=compromise_channel_id))
    critical_channel_id = int(config.get("channels", "critical_channel_id", fallback=critical_channel_id))
    debug_channel_id = int(config.get("channels", "debug_channel_id", fallback=debug_channel_id))
    exchange_channel_id = int(config.get("channels", "exchange_channel_id", fallback=exchange_channel_id))
    hide_channel_id = int(config.get("channels", "hide_channel_id", fallback=hide_channel_id))
    test_group_id = int(config.get("channels", "test_group_id", fallback=test_group_id))
    tip_channel_id = int(config.get("channels", "tip_channel_id", fallback=tip_channel_id))

    # [custom]
    default_group_link = config.get("custom", "default_group_link", fallback=default_group_link)
    leave_button = config.get("custom", "leave_button", fallback=leave_button)
    leave_link = config.get("custom", "leave_link", fallback=leave_link)
    leave_reason = config.get("custom", "leave_reason", fallback=leave_reason)
    manual_link = config.get("custom", "manual_link", fallback=manual_link)
    project_link = config.get("custom", "project_link", fallback=project_link)
    project_name = config.get("custom", "project_name", fallback=project_name)

    # [emoji]
    emoji_ad_single = int(config.get("emoji", "emoji_ad_single", fallback=emoji_ad_single))
    emoji_ad_total = int(config.get("emoji", "emoji_ad_total", fallback=emoji_ad_total))
    emoji_many = int(config.get("emoji", "emoji_many", fallback=emoji_many))
    emoji_protect = config.get("emoji", "emoji_protect", fallback=emoji_protect).encode()
    emoji_protect = getdecoder("unicode_escape")(emoji_protect)[0]
    emoji_wb_single = int(config.get("emoji", "emoji_wb_single", fallback=emoji_wb_single))
    emoji_wb_total = int(config.get("emoji", "emoji_wb_total", fallback=emoji_wb_total))

    # [encrypt]
    key = config.get("encrypt", "key", fallback=key)
    key = key.encode("utf-8")
    password = config.get("encrypt", "password", fallback=password)

    # [language]
    lang = config.get("language", "lang", fallback=lang)
    normalize = config.get("language", "normalize", fallback=normalize)
    normalize = eval(normalize)

    # [mode]
    aio = config.get("mode", "aio", fallback=aio)
    aio = eval(aio)
    backup = config.get("mode", "backup", fallback=backup)
    backup = eval(backup)

    # [time]
    date_reset = config.get("time", "date_reset", fallback=date_reset)
    time_channel = int(config.get("time", "time_channel", fallback=time_channel))
    time_keyword = int(config.get("time", "time_keyword", fallback=time_keyword))
    time_ot = int(config.get("time", "time_ot", fallback=time_ot))
    time_rm = int(config.get("time", "time_rm", fallback=time_rm))
    time_welcome = int(config.get("time", "time_welcome", fallback=time_welcome))

    # [flag]
    broken = False
except Exception as e:
    print("[ERROR] Read data from config.ini error, please check the log file")
    logger.warning(f"Read data from config.ini error: {e}", exc_info=True)

# Check
check_all(
    {
        "basic": {
            "bot_token": bot_token,
            "prefix": prefix
        },
        "bots": {
            "avatar_id": avatar_id,
            "captcha_id": captcha_id,
            "clean_id": clean_id,
            "index_id": index_id,
            "lang_id": lang_id,
            "long_id": long_id,
            "noflood_id": noflood_id,
            "noporn_id": noporn_id,
            "nospam_id": nospam_id,
            "tip_id": tip_id,
            "user_id": user_id,
            "warn_id": warn_id
        },
        "channels": {
            "compromise_channel_id": compromise_channel_id,
            "critical_channel_id": critical_channel_id,
            "debug_channel_id": debug_channel_id,
            "exchange_channel_id": exchange_channel_id,
            "hide_channel_id": hide_channel_id,
            "test_group_id": test_group_id,
            "tip_channel_id": tip_channel_id
        },
        "custom": {
            "default_group_link": default_group_link,
            "leave_button": leave_button,
            "leave_link": leave_link,
            "leave_reason": leave_reason,
            "manual_link": manual_link,
            "project_link": project_link,
            "project_name": project_name
        },
        "emoji": {
            "emoji_ad_single": emoji_ad_single,
            "emoji_ad_total": emoji_ad_total,
            "emoji_many": emoji_many,
            "emoji_protect": emoji_protect,
            "emoji_wb_single": emoji_wb_single,
            "emoji_wb_total": emoji_wb_total
        },
        "encrypt": {
            "key": key,
            "password": password
        },
        "language": {
            "lang": lang,
            "normalize": normalize
        },
        "mode": {
            "aio": aio,
            "backup": backup
        },
        "time": {
            "date_reset": date_reset,
            "time_channel": time_channel,
            "time_keyword": time_keyword,
            "time_ot": time_ot,
            "time_rm": time_rm,
            "time_welcome": time_welcome
        }
    },
    broken
)

# Language Dictionary
lang_dict: dict = {}
LANG_PATH = CUSTOM_LANG_PATH if exists(CUSTOM_LANG_PATH) else f"languages/{lang}.yml"

try:
    with open(LANG_PATH, "r", encoding="utf-8") as f:
        lang_dict = safe_load(f)
except Exception as e:
    logger.critical(f"Reading language YAML file failed: {e}", exc_info=True)
    raise SystemExit("Reading language YAML file failed")

# Init

all_commands: List[str] = [
    "channel",
    "clear",
    "config",
    "config_tip",
    "find_pin",
    "hold",
    "keyword",
    "keywords",
    "kws",
    "ot",
    "resend",
    "restart",
    "rm",
    "show",
    "start",
    "update",
    "version",
    "welcome"
]

bot_ids: Set[int] = {avatar_id, captcha_id, clean_id, index_id, lang_id, long_id,
                     noflood_id, noporn_id, nospam_id, tip_id, user_id, warn_id}

chats: Dict[int, Chat] = {}
# chats = {
#     -10012345678: Chat
# }

declared_message_ids: Dict[int, Set[int]] = {}
# declared_message_ids = {
#     -10012345678: {123}
# }

default_channel_data: Dict[str, Union[int, str]] = {
    "aid": 0,
    "cid": 0,
    "mid": 0,
    "time": 0,
    "text": lang_dict.get("description_channel"),
    "button": lang_dict.get("button_channel"),
    "link": ""
}

default_config: Dict[str, Union[bool, int]] = {
    "default": True,
    "lock": 0,
    "captcha": True,
    "alone": False,
    "clean": True,
    "ot": True,
    "rm": True,
    "welcome": True,
    "keyword": True,
    "white": False,
    "equal": False,
    "cancel": False,
    "hold": False,
    "channel": False,
    "resend": False
}

default_keyword_data: Dict[str, Union[int, Dict[str, Dict[str, Union[int, str, Set[str]]]]]] = {
    "lock": 0,
    "aid": 0,
    "kws": {}
}

default_message_data: Dict[str, Union[Dict[str, Tuple[int, int]], Tuple[int, int]]] = {
    "keywords": {},
    "ot": (0, 0),
    "rm": (0, 0),
    "welcome": (0, 0)
}

default_ot_data: Dict[str, Union[int, str]] = {
    "aid": 0,
    "reply": lang_dict.get("description_ot"),
    "old": ""
}

default_rm_data: Dict[str, Union[int, str]] = {
    "aid": 0,
    "reply": lang_dict.get("description_rm"),
    "old": "",
    "count": 0,
    "today": 0
}

default_user_status: Dict[str, Dict[str, float]] = {
    "score": {
        "captcha": 0.0,
        "clean": 0.0,
        "lang": 0.0,
        "long": 0.0,
        "noflood": 0.0,
        "noporn": 0.0,
        "nospam": 0.0,
        "warn": 0.0
    }
}

default_welcome_data: Dict[str, Union[int, str]] = {
    "aid": 0,
    "reply": lang_dict.get("description_welcome"),
    "old": "",
    "count": 0,
    "today": 0
}

emoji_set: Set[str] = {v for k, v in vars(emoji).items() if not k.startswith("_")}

hold_ids: Dict[int, str] = {}
# hold_ids = {
#     -10012345678: "random"
# }

keyworded_ids: Dict[int, Dict[int, Set[str]]] = {}
# keyworded_ids = {
#     -10012345678: {
#         12345678: {"tag"}
#     }
# }

locks: Dict[str, Lock] = {
    "admin": Lock(),
    "channel": Lock(),
    "config": Lock(),
    "message": Lock(),
    "receive": Lock(),
    "regex": Lock()
}

members: Dict[int, Dict[int, ChatMember]] = {}
# members = {
#     -10012345678: {
#         12345678: ChatMember
#     }
# }

receivers: Dict[str, List[str]] = {
    "declare": ["ANALYZE", "AVATAR", "CAPTCHA", "CLEAN", "LANG", "LONG",
                "NOFLOOD", "NOPORN", "NOSPAM", "TIP", "USER", "WARN", "WATCH"]
}

regex: Dict[str, bool] = {
    "ad": False,
    "ban": False,
    "bio": False,
    "con": False,
    "del": False,
    "fcnm": False,
    "fil": False,
    "iml": False,
    "pho": False,
    "nm": False,
    "rm": True,
    "sho": False,
    "spc": False,
    "spe": False,
    "tgl": False,
    "wb": False
}

for c in ascii_lowercase:
    regex[f"ad{c}"] = False

sender: str = "TIP"

should_hide: bool = False

started_ids: Set[int] = set()
# started_ids = {12345678}

updating: bool = False

version: str = "0.2.7"

welcomed_ids: Dict[int, Set[int]] = {}
# welcomed_ids = {
#     -10012345678: {12345678}
# }

# Load data from TXT file

if exists(JOIN_PATH):
    with open(JOIN_PATH, "r", encoding="utf-8") as f:
        join_text = f.read()
else:
    join_text = ""

if exists(START_PATH):
    with open(START_PATH, "r", encoding="utf-8") as f:
        start_text = f.read()
else:
    start_text = ""

# Load data from pickle

# Init ids variables

admin_ids: Dict[int, Set[int]] = {}
# admin_ids = {
#     -10012345678: {12345678}
# }

bad_ids: Dict[str, Set[int]] = {
    "channels": set(),
    "users": set()
}
# bad_ids = {
#     "channels": {-10012345678},
#     "users": {12345678}
# }

flooded_ids: Set[int] = set()
# flooded_ids = {-10012345678}

group_ids: Dict[str, int] = {
    "captcha": 0,
    "manage": 0,
    "regex": 0,
    "ticket": 0
}

ignore_ids: Dict[str, Set[int]] = {
    "nospam": set(),
    "user": set()
}
# ignore_ids = {
#     "nospam": {-10012345678},
#     "user": {-10012345678}
# }

lack_group_ids: Set[int] = set()
# lack_group_ids = {-10012345678}

left_group_ids: Set[int] = set()
# left_group_ids = {-10012345678}

member_ids: Dict[int, Set[int]] = {}
# member_ids = {
#     -10012345678: {12345678}
# }

message_ids: Dict[int, Dict[str, Union[Dict[str, Tuple[int, int]], Tuple[int, int]]]] = {}
# message_ids = {
#     -10012345678: {
#         "keywords": {
#             "tag": (124, 1512345678)
#         },
#         "ot": (125, 1512345678),
#         "rm": (126, 1512345678),
#         "welcome": (127, 1512345678)
#     }
# }

pinned_ids: Dict[int, int] = {}
# pinned_ids = {
#     -10012345678: 123
# }

trust_ids: Dict[int, Set[int]] = {}
# trust_ids = {
#     -10012345678: {12345678}
# }

user_ids: Dict[int, Dict[str, Dict[str, float]]] = {}
# user_ids = {
#     12345678: {
#         "score": {
#             "captcha": 0.0,
#             "clean": 0.0,
#             "lang": 0.0,
#             "long": 0.0,
#             "noflood": 0.0,
#             "noporn": 0.0,
#             "nospam": 0.0,
#             "warn": 0.0
#         }
#     }
# }

watch_ids: Dict[str, Dict[int, int]] = {
    "ban": {},
    "delete": {}
}
# watch_ids = {
#     "ban": {
#         12345678: 1512345678
#     },
#     "delete": {
#         12345678: 1512345678
#     }
# }

white_ids: Set[int] = set()
# white_ids = {12345678}

# Init data variables

channels: Dict[int, Dict[str, Union[int, str]]] = {}
# channels = {
#     -10012345678: {
#         "aid": 12345678,
#         "cid": -10012345678,
#         "mid": 123,
#         "time": 1512345678,
#         "text": "text",
#         "button": "text",
#         "link": ""
#     }
# }

configs: Dict[int, Dict[str, Union[bool, int, str]]] = {}
# configs = {
#     -10012345678: {
#         "default": True,
#         "lock": 0,
#         "captcha": True,
#         "alone": False,
#         "clean": True,
#         "ot": True,
#         "rm": True,
#         "welcome": True,
#         "keyword": True,
#         "white": True,
#         "equal": False,
#         "cancel": False,
#         "hold": False,
#         "channel": False,
#         "resend": False
#     }
# }

current: str = ""
# current = "0.0.1"

keywords: Dict[int, Dict[str, Union[int, Dict[str, Dict[str, Union[int, str, Set[str]]]]]]] = {}
# keywords = {
#     -10012345678: {
#         "lock": 1512345678,
#         "aid": 12345678,
#         "kws": {
#             "tag": {
#                 "time": 1512345678,
#                 "aid": 12345678,
#                 "words": {"keyword1", "keyword2"},
#                 "reply": "text",
#                 "modes": {"include"},
#                 "actions": {"reply"},
#                 "target": "member",
#                 "destruct": 300,
#                 "raw": "text",
#                 "count": 0,
#                 "today": 0
#             }
#         }
#
#     }
# }

ots: Dict[int, Dict[str, Union[int, str]]] = {}
# ots = {
#     -10012345678: {
#         "aid": 12345678,
#         "reply": "text",
#         "old": "old reply"
#     }
# }

rms: Dict[int, Dict[str, Union[int, str]]] = {}
# rms = {
#     -10012345678: {
#         "aid": 12345678,
#         "reply": "text",
#         "old": "old reply",
#         "count": 8,
#         "today": 1
#     }
# }

starts: Dict[str, Dict[str, Union[bool, int, str]]] = {}
# starts = {
#     "random": {
#         "until": 1512345678,
#         "cid": -10012345678,
#         "uid": 12345678,
#         "action": "act",
#         "active": False
#     }
# }

timeout_words: Set[str] = set()
# timeout_words = {"timeout_regex"}

token: str = ""
# token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

welcomes: Dict[int, Dict[str, Union[int, str]]] = {}
# welcomes = {
#     -10012345678: {
#         "aid": 12345678,
#         "reply": "text",
#         "old": "old reply",
#         "count": 8,
#         "today": 1
#     }
# }

# Init word variables

for word_type in regex:
    locals()[f"{word_type}_words"]: Dict[str, Dict[str, Union[float, int]]] = {}

# type_words = {
#     "regex": 0
# }

# Load data
file_list: List[str] = ["admin_ids", "bad_ids", "flooded_ids", "group_ids", "ignore_ids", "lack_group_ids",
                        "left_group_ids", "member_ids", "message_ids", "pinned_ids", "trust_ids", "user_ids",
                        "watch_ids", "white_ids",
                        "channels", "configs", "current", "keywords", "ots", "rms", "starts", "timeout_words",
                        "token", "welcomes"]
file_list += [f"{f}_words" for f in regex]

for file in file_list:
    try:
        try:
            if exists(f"{PICKLE_PATH}/{file}") or exists(f"{PICKLE_BACKUP_PATH}/{file}"):
                with open(f"{PICKLE_PATH}/{file}", "rb") as f:
                    locals()[f"{file}"] = pickle.load(f)
            else:
                with open(f"{PICKLE_PATH}/{file}", "wb") as f:
                    pickle.dump(eval(f"{file}"), f)
        except Exception as e:
            logger.error(f"Load data {file} error: {e}", exc_info=True)

            with open(f"{PICKLE_BACKUP_PATH}/{file}", "rb") as f:
                locals()[f"{file}"] = pickle.load(f)
    except Exception as e:
        logger.critical(f"Load data {file} backup error: {e}", exc_info=True)
        raise SystemExit("[DATA CORRUPTION]")

# Generate special characters dictionary
for special in ["spc", "spe"]:
    locals()[f"{special}_dict"]: Dict[str, str] = {}

    for rule in locals()[f"{special}_words"]:
        # Check keys
        if "[" not in rule:
            continue

        # Check value
        if "?#" not in rule:
            continue

        keys = rule.split("]")[0][1:]
        value = rule.split("?#")[1][1]

        for k in keys:
            locals()[f"{special}_dict"][k] = value

# Start program
copyright_text = (f"SCP-079-{sender} v{version}, Copyright (C) 2019-2020 SCP-079 <https://scp-079.org>\n"
                  "Licensed under the terms of the GNU General Public License v3 or later (GPLv3+)\n")
print(copyright_text)
