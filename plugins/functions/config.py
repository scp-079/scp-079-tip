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
from copy import deepcopy
from re import search
from typing import Dict, List, Set, Union

from pyrogram import Client
from pyrogram.types import Message

from .. import glovar
from .channel import send_debug
from .command import command_error
from .decorators import threaded
from .etc import code, code_block, general_link, get_int, get_now, get_text_user, lang, thread
from .file import delete_file, file_txt, save
from .markup import get_text_and_markup_tip
from .telegram import get_group_info, send_document, send_message, send_report_message

# Enable logging
logger = logging.getLogger(__name__)


def conflict_config(config: dict, config_list: List[str], master: str) -> dict:
    # Conflict config
    result = config

    try:
        if master not in config_list:
            return config

        if not config.get(master, False):
            return config

        config_list.remove(master)

        for other in config_list:
            result[other] = False
    except Exception as e:
        logger.warning(f"Conflict config error: {e}", exc_info=True)

    return result


def get_config_text(config: dict) -> str:
    # Get the group's config text
    result = ""

    try:
        # Basic
        default_text = (lambda x: lang("default") if x else lang("custom"))(config.get("default"))
        result += f"{lang('config')}{lang('colon')}{code(default_text)}\n"

        # Others
        for the_type in ["captcha", "alone", "clean", "ot", "rm", "welcome", "keyword", "white",
                         "cancel", "hold", "channel", "resend"]:
            the_text = (lambda x: lang("enabled") if x else lang("disabled"))(config.get(the_type))
            result += f"{lang(the_type)}{lang('colon')}{code(the_text)}\n"
    except Exception as e:
        logger.warning(f"Get config text error: {e}", exc_info=True)

    return result


def kws_action(text: str) -> str:
    # Get kws action string
    result = ""

    try:
        if text in {"reply", "delete", "kick", "ban", "restrict"}:
            return lang(f"kws_actions_{text}")

        if text.startswith("ban-") or text.startswith("restrict-"):
            time = text.split("-")[1]
            return lang(f"kws_actions_{text}_time").format(time)

    except Exception as e:
        logger.warning(f"Kws action error: {e}", exc_info=True)

    return result


def kws_add(client: Client, message: Message, gid: int, key: str, text: str, the_type: str = "add") -> bool:
    # Add or edit a custom keyword
    result = False

    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        now = get_now()

        # Check keywords count
        if the_type == "add" and len(glovar.keywords[gid]["kws"]) >= 100:
            return command_error(client, message, lang(f"action_kws_{the_type}"), lang("error_exceed_kws"),
                                 report=False, private=True)

        # Check the text
        if len(text) > 3000:
            return command_error(client, message, lang(f"action_kws_{the_type}"), lang("command_para"),
                                 lang("error_exceed_raw"), report=False, private=True)

        # Get text list
        text_list = kws_get(text)

        # Check the text list
        if not text_list:
            return command_error(client, message, lang(f"action_kws_{the_type}"), lang("command_para"),
                                 report=False, private=True)

        # Get keywords
        words = {w.strip() for w in text_list[0].split("||") if w.strip()}

        # Check the words
        if not words:
            return command_error(client, message, lang(f"action_kws_{the_type}"), lang("command_para"),
                                 report=False, private=True)

        # Get reply
        reply = text_list[1]
        _, markup = get_text_and_markup_tip(gid, reply)
        
        # Check the reply
        if len(reply) > 1500:
            return command_error(client, message, lang(f"action_kws_{the_type}"), lang("command_para"),
                                 lang("error_exceed_reply"), report=False, private=True)
        elif markup is False:
            return command_error(client, message, lang(f"action_kws_{the_type}"), lang("command_para"),
                                 lang("error_markup_invalid"), report=False, private=True)
        elif markup and sum(len(m) for m in markup.inline_keyboard) > 6:
            return command_error(client, message, lang(f"action_kws_{the_type}"), lang("command_para"),
                                 lang("error_exceed_button"), report=False, private=True)

        # Get modes
        modes = {m.strip() for m in text_list[2].split() if m.strip()}

        # Check the modes
        if not modes or not all(m in {"include", "exact", "case", "name", "forward", "pure"} for m in modes):
            return command_error(client, message, lang(f"action_kws_{the_type}"), lang("command_para"),
                                 lang("error_kws_modes_invalid"), report=False, private=True)
        elif not any(m in {"include", "exact"} for m in modes):
            return command_error(client, message, lang(f"action_kws_{the_type}"), lang("command_para"),
                                 lang("error_kws_modes_lack"), report=False, private=True)
        elif "include" in modes and "exact" in modes:
            return command_error(client, message, lang(f"action_kws_{the_type}"), lang("command_para"),
                                 lang("error_kws_modes_conflict"), report=False, private=True)

        # Get the actions
        actions = {a.strip() for a in text_list[3].split() if a.strip()}

        if not actions or not all(a in {"reply", "delete", "kick", "ban", "restrict"}
                                  or search(r"^ban-\d{3,8}$", a)
                                  or search(r"^restrict-\d{3,8}$", a)
                                  for a in actions):
            return command_error(client, message, lang(f"action_kws_{the_type}"), lang("command_para"),
                                 lang("error_kws_actions_invalid"), report=False, private=True)
        elif len([a for a in actions if a == "kick" or a.startswith("ban") or a.startswith("restrict")]) > 1:
            return command_error(client, message, lang(f"action_kws_{the_type}"), lang("command_para"),
                                 lang("error_kws_actions_conflict"), report=False, private=True)

        # Get target
        target = text_list[4]

        # Check the target
        if target not in {"member", "admin", "all"}:
            return command_error(client, message, lang(f"action_kws_{the_type}"), lang("command_para"),
                                 lang("error_kws_target_invalid"), report=False, private=True)

        # Get destruct
        destruct = text_list[5]

        # Check the destruct
        if not search(r"^\d{3,5}$", destruct):
            return command_error(client, message, lang(f"action_kws_{the_type}"), lang("command_para"),
                                 lang("error_kws_destruct_invalid"), report=False, private=True)
        
        if the_type == "add":
            glovar.keywords[gid]["kws"][key] = {
                "time": now,
                "aid": aid,
                "words": words,
                "reply": reply,
                "modes": modes,
                "actions": actions,
                "target": target,
                "destruct": get_int(destruct),
                "raw": text,
                "count": 0,
                "today": 0
            }
        else:
            glovar.keywords[gid]["kws"][key]["time"] = now
            glovar.keywords[gid]["kws"][key]["aid"] = aid
            glovar.keywords[gid]["kws"][key]["words"] = words
            glovar.keywords[gid]["kws"][key]["reply"] = reply
            glovar.keywords[gid]["kws"][key]["modes"] = modes
            glovar.keywords[gid]["kws"][key]["actions"] = actions
            glovar.keywords[gid]["kws"][key]["target"] = target
            glovar.keywords[gid]["kws"][key]["destruct"] = get_int(destruct)
            glovar.keywords[gid]["kws"][key]["raw"] = text
        
        # Save the data
        save("keywords")

        # Generate the text and the markup
        group_name, group_link = get_group_info(client, gid)
        text = (f"{lang('group_name')}{lang('colon')}{general_link(group_name, group_link)}\n"
                f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang(f'action_kws_{the_type}'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n" + code("-" * 24) + "\n"
                f"{lang('kws_key')}{lang('colon')}{code(key)}\n" + code("-" * 24) + "\n"
                f"{lang('keyword')}{lang('colon')}{code(lang('comma').join(words))}\n" + code("-" * 24) + "\n")
        reply_text, markup = get_text_and_markup_tip(gid, reply)
        reply_text = get_text_user(reply_text, message.from_user)
        text += reply_text

        # Send the report message
        thread(send_message, (client, cid, text, mid, markup))

        result = True
    except Exception as e:
        logger.warning(f"Kws add error: {e}", exc_info=True)

    return result


def kws_config_occupy(gid: int, uid: int) -> bool:
    # Kws config occupy
    result = False

    try:
        for group_id in list(glovar.keywords):
            if glovar.keywords[group_id]["aid"] != uid:
                continue

            if group_id == gid:
                continue

            glovar.keywords[group_id]["lock"] = 0
            glovar.keywords[group_id]["aid"] = 0
    except Exception as e:
        logger.warning(f"Kws config occupy error: {e}", exc_info=True)

    return result


def kws_config_gid(uid: int, now: int) -> int:
    # Kws config get gid
    result = 0

    try:
        for group_id in list(glovar.keywords):
            if now >= glovar.keywords[group_id]["lock"] + 600:
                continue

            if glovar.keywords[group_id]["aid"] != uid:
                continue

            return group_id
    except Exception as e:
        logger.warning(f"Kws config gid error: {e}", exc_info=True)

    return result


def kws_get(text: str) -> List[str]:
    # Get keyword settings
    result = []

    try:
        # Check the text
        if not text.strip():
            return []

        # Get text list
        text_list = [t.strip() for t in text.split("\n+++\n") if t.strip()]

        # Check the text list
        if not text_list or len(text_list) < 2:
            return []

        # Check modes
        if len(text_list) < 3:
            text_list.append("include")

        # Check actions
        if len(text_list) < 4:
            text_list.append("reply")

        # Check target
        if len(text_list) < 5:
            text_list.append("all")

        # Check destruct
        if len(text_list) < 6:
            text_list.append(str(glovar.time_keyword))

        # Get result
        result = text_list
    except Exception as e:
        logger.warning(f"Kws get error: {e}", exc_info=True)

    return result


def kws_remove(client: Client, message: Message, gid: int, key: str) -> bool:
    # Remove a custom keyword
    result = False

    try:
        # Basic data
        cid = message.chat.id
        mid = message.message_id
        words = glovar.keywords[gid]["kws"][key]["words"]

        # Pop the data
        glovar.keywords[gid]["kws"].pop(key, {})
        save("keywords")

        # Generate the text
        group_name, group_link = get_group_info(client, gid)
        text = (f"{lang('group_name')}{lang('colon')}{general_link(group_name, group_link)}\n"
                f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_kws_remove'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n" + code("-" * 24) + "\n"
                f"{lang('kws_key')}{lang('colon')}{code(key)}\n" + code("-" * 24) + "\n"
                f"{lang('keyword')}{lang('colon')}{code(lang('comma').join(words))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        result = True
    except Exception as e:
        logger.warning(f"Kws remove error: {e}", exc_info=True)

    return result


@threaded()
def kws_show(client: Client, message: Message, gid: int, file: bool = False) -> bool:
    # Show all custom keywords
    result = False

    try:
        # Basic data
        cid = message.chat.id
        mid = message.message_id

        # Get keywords
        with glovar.locks["config"]:
            keywords = glovar.keywords[gid]["kws"]

        # Check data
        if not keywords:
            return command_error(client, message, lang("action_kws_show"), lang("error_none"),
                                 report=False, private=True)

        # Send as file
        if file or len(keywords) > 5:
            return kws_show_file(client, message, gid, keywords)

        # Generate the text
        group_name, group_link = get_group_info(client, gid)
        text = (f"{lang('group_name')}{lang('colon')}{general_link(group_name, group_link)}\n"
                f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_kws_show'))}\n"
                f"{lang('kws_total')}{lang('colon')}{code(len(keywords))}\n\n")

        for key in keywords:
            aid = keywords[key]["aid"]
            keyword = f"{lang('comma')}".join(keywords[key]["words"])
            modes = f"{lang('comma')}".join(lang(f"kws_modes_{m}") for m in keywords[key]["modes"])
            actions = f"{lang('comma')}".join(kws_action(a) for a in keywords[key]["actions"])
            target = lang(f"kws_target_{keywords[key]['target']}")
            destruct = f"{keywords[key]['destruct']} {lang('seconds')}"
            count = f"{keywords[key]['count']} {lang('times')}"
            today = f"{keywords[key]['today']} {lang('times')}"
            raw = keywords[key]['raw'].strip()
            text += code("-" * 24) + "\n\n"
            text += (f"{lang('kws_key')}{lang('colon')}{code(key)}\n"
                     f"{lang('modified_by')}{lang('colon')}{code(aid)}\n"
                     f"{lang('keyword')}{lang('colon')}{code(keyword)}\n"
                     f"{lang('kws_modes')}{lang('colon')}{code(modes)}\n"
                     f"{lang('kws_actions')}{lang('colon')}{code(actions)}\n"
                     f"{lang('kws_target')}{lang('colon')}{code(target)}\n"
                     f"{lang('kws_destruct')}{lang('colon')}{code(destruct)}\n"
                     f"{lang('kws_count')}{lang('colon')}{code(count)}\n"
                     f"{lang('kws_today')}{lang('colon')}{code(today)}\n"
                     f"{lang('kws_raw')}{lang('colon')}{code('-' * 16)}\n\n"
                     f"{code_block(raw)}\n\n")

        # Send as file
        if len(text) > 4000:
            return kws_show_file(client, message, gid, keywords)

        # Send the report message
        result = bool(send_message(client, cid, text, mid))
    except Exception as e:
        logger.warning(f"Kws show error: {e}", exc_info=True)

    return result


def kws_show_file(client: Client, message: Message, gid: int,
                  keywords: Dict[str, Dict[str, Union[int, str, Set[str]]]]) -> bool:
    # Show all custom keywords as TXT file
    result = False

    try:
        # Basic data
        cid = message.chat.id
        mid = message.message_id

        # Generate the text
        group_name, group_link = get_group_info(client, gid)
        caption = (f"{lang('group_name')}{lang('colon')}{general_link(group_name, group_link)}\n"
                   f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                   f"{lang('action')}{lang('colon')}{code(lang('action_kws_show'))}\n\n")
        text = (f"{lang('group_name')}{lang('colon')}{group_name}\n"
                f"{lang('group_id')}{lang('colon')}{gid}\n"
                f"{lang('kws_total')}{lang('colon')}{len(keywords)}\n\n")

        for key in keywords:
            aid = keywords[key]["aid"]
            keyword = f"{lang('comma')}".join(keywords[key]["words"])
            modes = f"{lang('comma')}".join(lang(f"kws_modes_{m}") for m in keywords[key]["modes"])
            actions = f"{lang('comma')}".join(kws_action(a) for a in keywords[key]["actions"])
            target = lang(f"kws_target_{keywords[key]['target']}")
            destruct = f"{keywords[key]['destruct']} {lang('seconds')}"
            count = f"{keywords[key]['count']} {lang('times')}"
            today = f"{keywords[key]['today']} {lang('times')}"
            raw = keywords[key]['raw'].strip()
            text += "-" * 24 + "\n\n"
            text += (f"{lang('kws_key')}{lang('colon')}{key}\n"
                     f"{lang('modified_by')}{lang('colon')}{aid}\n"
                     f"{lang('keyword')}{lang('colon')}{keyword}\n"
                     f"{lang('kws_modes')}{lang('colon')}{modes}\n"
                     f"{lang('kws_actions')}{lang('colon')}{actions}\n"
                     f"{lang('kws_target')}{lang('colon')}{target}\n"
                     f"{lang('kws_destruct')}{lang('colon')}{destruct}\n"
                     f"{lang('kws_count')}{lang('colon')}{count}\n"
                     f"{lang('kws_today')}{lang('colon')}{today}\n"
                     f"{lang('kws_raw')}{lang('colon')}{'-' * 16}\n\n"
                     f"{raw}\n\n")

        # Save to a file
        file = file_txt(text)

        # Send the report message
        send_document(client, cid, file, None, caption, mid)

        # Delete the file
        thread(delete_file, (file,))

        result = True
    except Exception as e:
        logger.warning(f"Kws show file error: {e}", exc_info=True)

    return result


def start_kws(client: Client, message: Message, key: str) -> bool:
    # Start kws
    result = False

    try:
        # Basic data
        cid = message.chat.id
        uid = message.from_user.id
        mid = message.message_id
        gid = glovar.starts[key]["cid"]
        aid = glovar.starts[key]["uid"]

        # Check the permission
        if uid != aid:
            return False

        # Send the report message
        group_name, group_link = get_group_info(client, gid)
        text = (f"{lang('group_name')}{lang('colon')}{general_link(group_name, group_link)}\n"
                f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_kws'))}\n"
                f"{lang('description')}{lang('colon')}{code(lang('description_kws'))}\n")
        thread(send_message, (client, cid, text, mid))

        result = True
    except Exception as e:
        logger.warning(f"Start kws error: {e}", exc_info=True)

    return result


def update_config(client: Client, message: Message, config: dict, more: str = "") -> bool:
    # Update a group's config
    result = False

    try:
        # Basic data
        gid = message.chat.id
        aid = message.from_user.id

        # Update the config
        glovar.configs[gid] = deepcopy(config)
        save("configs")

        # Send the report message
        text = (f"{lang('admin_group')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('config_change'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n")

        if more:
            text += f"{lang('more')}{lang('colon')}{code(more)}\n"

        send_report_message(15, client, gid, text)

        # Send the debug message
        send_debug(
            client=client,
            gids=[gid],
            action=lang("config_change"),
            aid=aid,
            more=more
        )

        result = True
    except Exception as e:
        logger.warning(f"Update config error: {e}", exc_info=True)

    return result
