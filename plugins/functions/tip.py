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
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, User

from .. import glovar
from .decorators import threaded
from .etc import code, get_now, get_replaced, get_text_user, lang
from .file import save
from .filters import is_keyworded_user, is_should_terminate
from .group import delete_message
from .markup import get_text_and_markup_tip
from .telegram import edit_message_text, export_chat_invite_link, send_message
from .user import terminate_user

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
        enabled = glovar.configs[gid].get("channel", False)
        cid = glovar.channels[gid].get("cid", 0)
        mid = glovar.channels[gid].get("mid", 0)
        time = glovar.channels[gid].get("time", 0)
        text = glovar.channels[gid].get("text")
        button = glovar.channels[gid].get("button")

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
            glovar.channels[gid]["mid"] = 0
            glovar.channels[gid]["time"] = 0
            save("channels")
            delete_message(client, cid, mid)
            return False
        elif not link:
            return False

        # Update the link
        glovar.channels[gid]["link"] = link
        save("channels")

        # Check the config
        if not enabled and the_type not in {"open", "resend"}:
            return False

        # Change the config
        if the_type == "close":
            glovar.configs[gid]["channel"] = False
            save("configs")
        elif the_type not in {"open", "resend"}:
            glovar.configs[gid]["channel"] = True
            save("configs")

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
                glovar.channels[gid]["mid"] = mid
                glovar.channels[gid]["time"] = now
                save("channels")
                return True
            elif result is False:
                return False

        # Send new message
        result = send_message(client, cid, text, None, markup)

        if not result:
            return False

        glovar.channels[gid]["mid"] = result.message_id
        glovar.channels[gid]["time"] = now
        save("channels")
        mid and delete_message(client, cid, mid)

        result = True
    except Exception as e:
        logger.warning(f"New invite link error: {e}", exc_info=True)
    finally:
        glovar.locks["channel"].release()

    return result


def tip_keyword(client: Client, message: Message, data: dict) -> bool:
    # Send keyword tip
    result = False

    try:
        # Basic data
        gid = message.chat.id
        uid = message.from_user.id
        key = data["key"]
        mid = data["mid"]
        reply = data["reply"]
        actions = data["actions"]
        destruct = data["destruct"]
        now = get_now()

        # Check terminate mode
        if is_should_terminate(message, actions):
            return terminate_user(client, message, data)

        # Get the user and message id
        if mid and message.reply_to_message:
            user = message.reply_to_message.from_user
            delete_message(client, gid, message.message_id)
        elif mid and not message.reply_to_message:
            return False
        elif not is_keyworded_user(gid, key, uid):
            user = message.from_user
            mid = message.message_id
        else:
            return False

        # Check reply action
        if "reply" not in actions:
            return False

        # Get the markup
        text, markup = get_text_and_markup_tip(gid, reply)
        text = get_replaced(text, gid, user, destruct)

        # Send the tip
        result = send_message(client, gid, text, mid, markup)

        if not result:
            return False

        mid, _ = glovar.message_ids[gid]["keywords"].get(key, (0, 0))
        mid and delete_message(client, gid, mid)
        glovar.message_ids[gid]["keywords"][key] = (result.message_id, now)
        save("message_ids")
        
        result = True
    except Exception as e:
        logger.warning(f"Tip keyword error: {e}", exc_info=True)

    return result


@threaded()
def tip_saved(client: Client, gid: int, user: User, key: str) -> bool:
    # Send saved tip
    result = False

    glovar.locks["message"].acquire()

    try:
        # Basic data
        now = get_now()

        # Get keyword
        keyword = glovar.keywords[gid]["kws"].get(key, {})

        # Check the keyword
        if not keyword:
            return False

        # Get the text and markup
        reply = keyword["reply"]
        text, markup = get_text_and_markup_tip(gid, reply)
        text = get_text_user(text, user)

        # Send the tip
        result = send_message(client, gid, text, None, markup)

        if not result:
            return False

        mid, _ = glovar.message_ids[gid]["keywords"].get(key, (0, 0))
        mid and delete_message(client, gid, mid)
        glovar.message_ids[gid]["keywords"][key] = (result.message_id, now)
        save("message_ids")

        result = True
    except Exception as e:
        logger.warning(f"Tip saved error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


@threaded()
def tip_ot(client: Client, gid: int, mid: int = None) -> bool:
    # Send OT tip
    result = False

    glovar.locks["message"].acquire()

    try:
        # Basic data
        now = get_now()
        reply = glovar.ots[gid].get("reply", "")

        # Check the config
        if not glovar.configs[gid].get("ot", True) or not reply:
            return False

        # Get the markup
        text, markup = get_text_and_markup_tip(gid, reply)

        # Send the tip
        result = send_message(client, gid, text, mid, markup)

        if not result:
            return False

        mid, _ = glovar.message_ids[gid]["ot"]
        mid and delete_message(client, gid, mid)
        glovar.message_ids[gid]["ot"] = (result.message_id, now)
        save("message_ids")
        
        result = True
    except Exception as e:
        logger.warning(f"Tip ot error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


@threaded()
def tip_rm(client: Client, gid: int, mid: int = None) -> bool:
    # Send RM tip
    result = False

    glovar.locks["message"].acquire()

    try:
        # Basic data
        now = get_now()
        reply = glovar.rms[gid].get("reply", "")

        # Check the config
        if not glovar.configs[gid].get("rm", True) or not reply:
            return False

        # Get the markup
        text, markup = get_text_and_markup_tip(gid, reply)

        # Send the tip
        result = send_message(client, gid, text, mid, markup)

        if not result:
            return False

        mid, _ = glovar.message_ids[gid]["rm"]
        mid and delete_message(client, gid, mid)
        glovar.message_ids[gid]["rm"] = (result.message_id, now)
        save("message_ids")
        
        result = True
    except Exception as e:
        logger.warning(f"Tip rm error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()
    
    return result


@threaded()
def tip_welcome(client: Client, user: User, gid: int = 0, mid: int = None, force: bool = False) -> bool:
    # Send welcome tip
    result = False

    glovar.locks["message"].acquire()

    try:
        # Basic data
        uid = user.id
        now = get_now()
        reply = glovar.welcomes[gid].get("reply", "")

        # Check the config
        if not glovar.configs[gid].get("welcome", True) or not reply:
            return False

        # Check welcome status
        if not force and uid in glovar.welcomed_ids[gid]:
            return False
        else:
            glovar.welcomed_ids[gid].add(uid)

        # Get the markup
        text, markup = get_text_and_markup_tip(gid, reply)

        # Get the alone mode
        if glovar.configs[gid].get("alone"):
            mid = None

        # Replace user field
        text = get_text_user(text, user)

        # Send the tip
        result = send_message(client, gid, text, mid, markup)

        if not result:
            return False

        mid, _ = glovar.message_ids[gid]["welcome"]
        mid and delete_message(client, gid, mid)
        glovar.message_ids[gid]["welcome"] = (result.message_id, now)
        save("message_ids")

        result = True
    except Exception as e:
        logger.warning(f"Tip welcome error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result
