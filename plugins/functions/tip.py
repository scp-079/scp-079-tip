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

from pyrogram import Client
from pyrogram.types import ChatMember, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import glovar
from .etc import code, get_full_name, get_now, lang, mention_id, mention_name
from .file import save
from .group import delete_message
from .telegram import edit_message_text, export_chat_invite_link, send_message


# Enable logging
logger = logging.getLogger(__name__)


def get_invite_link(client: Client, the_type: str, gid: int, manual: bool = False, reason: str = "") -> bool:
    # Get a new invite link
    result = False

    glovar.locks["channel"].acquire()

    try:
        # Basic data
        now = get_now()

        # Read the config
        cid = glovar.channels[gid].get("cid", 0)
        text = glovar.channels[gid].get("text")
        button = glovar.channels[gid].get("button")
        mid, time = glovar.message_ids[gid].get("channel", (0, 0))

        # Check the config
        if not cid:
            return False

        # Check the link time
        if not manual and the_type != "send" and now - time < glovar.time_channel:
            return False

        # Generate link
        link = export_chat_invite_link(client, gid)

        # Check the link
        if link is False:
            glovar.channels[gid]["cid"] = 0
            save("channels")
            glovar.message_ids[gid]["channel"] = (0, 0)
            save("message_ids")
            delete_message(client, cid, mid)
            return False
        elif not link:
            return False

        # Update the link
        glovar.channels[gid]["link"] = link
        save("channels")

        # Generate markup
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=button,
                        url=link
                    )
                ]
            ]
        )

        # Edit message
        if the_type in {"close", "edit", "open"} and mid:
            if the_type == "close":
                text = f"{lang('description')}{lang('colon')}{code(lang('description_close'))}\n"

                if reason:
                    text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

                markup = None

            result = edit_message_text(client, cid, mid, text, markup)

            if result:
                glovar.message_ids[gid]["channel"] = (mid, now)
                save("message_ids")
                return True
            elif result is False:
                return False

        # Send new message
        result = send_message(client, cid, text, None, markup)

        if not result:
            return False

        glovar.message_ids[gid]["channel"] = (result.message_id, now)
        save("message_ids")
        mid and delete_message(client, cid, mid)

        result = True
    except Exception as e:
        logger.warning(f"New invite link error: {e}", exc_info=True)
    finally:
        glovar.locks["channel"].release()

    return result


def get_words(words: set, exact: bool) -> dict:
    # Get words dict
    result = {}

    try:
        for word in words:
            if word.startswith("{{") and word.sendswith("}}"):
                word = word[2:-2]

                if not word:
                    continue

                result[word] = True
            elif exact:
                result[word] = True
            else:
                result[word] = False
    except Exception as e:
        logger.warning(f"Get words error: {e}", exc_info=True)

    return result


def tip_keyword(client: Client, message: Message, text: str, mid: int) -> bool:
    # Send keyword tip
    try:
        # Basic data
        gid = message.chat.id

        if mid:
            delete_message(client, gid, message.message_id)
        else:
            uid = message.from_user.id

            if text in glovar.keyworded_ids[gid].get(uid, set()):
                return True

            if not glovar.keyworded_ids[gid].get(uid, set()):
                glovar.keyworded_ids[gid][uid] = set()

            glovar.keyworded_ids[gid][uid].add(text)
            mid = message.message_id

        now = get_now()

        # Get the markup
        markup = get_markup("keyword", gid)

        # Send the tip
        result = send_message(client, gid, text, mid, markup)

        if result:
            mid, _ = glovar.message_ids[gid]["keyword"]
            mid and delete_message(client, gid, mid)
            glovar.message_ids[gid]["keyword"] = (result.message_id, now)
            save("message_ids")
        
        return True
    except Exception as e:
        logger.warning(f"Tip keyword error: {e}", exc_info=True)

    return False


def tip_ot(client: Client, gid: int, mid: int = None) -> bool:
    # Send OT tip
    try:
        # Basic data
        now = get_now()
        
        # Get the markup
        markup = get_markup("ot", gid)
        
        # Read the config
        text = glovar.configs[gid].get("ot_text")

        # Check the config
        if not glovar.configs[gid].get("ot") or not text:
            return True
        
        # Send the tip
        result = send_message(client, gid, text, mid, markup)

        if result:
            mid, _ = glovar.message_ids[gid]["ot"]
            mid and delete_message(client, gid, mid)
            glovar.message_ids[gid]["ot"] = (result.message_id, now)
            save("message_ids")
        
        return True
    except Exception as e:
        logger.warning(f"Tip ot error: {e}", exc_info=True)

    return False


def tip_rm(client: Client, gid: int, text: str, mid: int = None) -> bool:
    # Send RM tip
    try:
        # Basic data
        now = get_now()

        # Check the config
        if not glovar.configs[gid].get("rm"):
            return True

        # Check the text
        if not text or not text.strip():
            return True

        # Get the markup
        markup = get_markup("rm", gid)

        # Send the tip
        result = send_message(client, gid, text, mid, markup)

        if result:
            mid, _ = glovar.message_ids[gid]["rm"]
            mid and delete_message(client, gid, mid)
            glovar.message_ids[gid]["rm"] = (result.message_id, now)
            save("message_ids")
        
        return True
    except Exception as e:
        logger.warning(f"Tip rm error: {e}", exc_info=True)
    
    return False


def tip_welcome(client: Client, message: Message = None,
                member: ChatMember = None, gid: int = 0, mid: int = None, force: bool = False) -> bool:
    # Send welcome tip
    try:
        # Basic data
        if message:
            if message.new_chat_members:
                user = message.new_chat_members[0]
            else:
                user = message.from_user

            gid = message.chat.id
            uid = user.id
            mid = message.message_id
        elif member and gid:
            if member.status not in {"member", "restricted"}:
                return True

            user = member.user
            uid = user.id
        else:
            return True

        name = get_full_name(user)
        now = get_now()

        # Check welcome status
        if not force and uid in glovar.welcomed_ids[gid]:
            return True
        else:
            glovar.welcomed_ids[gid].add(uid)

        # Get the markup
        markup = get_markup("welcome", gid)

        # Read the config
        text = glovar.configs[gid].get("welcome_text")

        # Check the config
        if not text:
            return True

        if glovar.configs[gid].get("alone"):
            mid = None

        # Replace
        text = text.replace("$code_id", code(uid))
        text = text.replace("$code_name", code(name))
        text = text.replace("$mention_id", mention_id(uid))
        text = text.replace("$mention_name", mention_name(user))

        # Send the tip
        result = send_message(client, gid, text, mid, markup)

        if result:
            mid, _ = glovar.message_ids[gid]["welcome"]
            mid and delete_message(client, gid, mid)
            glovar.message_ids[gid]["welcome"] = (result.message_id, now)
            save("message_ids")

        return True
    except Exception as e:
        logger.warning(f"Tip welcome error: {e}", exc_info=True)

    return False
