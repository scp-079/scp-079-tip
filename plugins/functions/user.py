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
from time import sleep
from typing import Optional, Union

from pyrogram import Client
from pyrogram.types import ChatPermissions, Message, User

from .. import glovar
from .channel import forward_evidence, send_debug
from .config import kws_action
from .decorators import threaded
from .etc import get_int, get_now, get_text_user, lang, random_str
from .file import save
from .filters import is_class_d_user
from .group import delete_message
from .markup import get_text_and_markup_tip
from .telegram import kick_chat_member, restrict_chat_member, send_message, unban_chat_member

# Enable logging
logger = logging.getLogger(__name__)


def add_start(until: int, cid: int, uid: int, action: str) -> str:
    # Add start
    result = ""

    try:
        key = random_str(8)

        while glovar.starts.get(key):
            key = random_str(8)

        glovar.starts[key] = {
            "until": until,
            "cid": cid,
            "uid": uid,
            "action": action,
            "active": False
        }
        save("starts")

        result = key
    except Exception as e:
        logger.warning(f"Add start error: {e}", exc_info=True)

    return result


@threaded()
def ban_user(client: Client, gid: int, uid: Union[int, str], until_date: int = 0, lock: bool = False) -> bool:
    # Ban a user
    result = False

    lock and glovar.locks["ban"].acquire()

    try:
        result = kick_chat_member(client, gid, uid, until_date)
    except Exception as e:
        logger.warning(f"Ban user error: {e}", exc_info=True)
    finally:
        lock and glovar.locks["ban"].release()

    return result


def get_action_text(actions: set) -> str:
    # Get action text
    result = ""

    try:
        if "delete" in actions:
            result = kws_action("delete")

        actions.discard("reply")
        actions.discard("delete")

        if not actions:
            return result

        result = kws_action(list(actions)[0])
    except Exception as e:
        logger.warning(f"Get action text error: {e}", exc_info=True)

    return result


def get_user_from_message(message: Message) -> Optional[User]:
    # Get user from message
    result = None

    try:
        result = message.from_user if not message.new_chat_members else message.new_chat_members[0]
    except Exception as e:
        logger.warning(f"Get user from message error: {e}", exc_info=True)

    return result


@threaded()
def kick_user(client: Client, gid: int, uid: Union[int, str], until_date: int = 0, lock: bool = False) -> bool:
    # Kick a user
    result = False

    lock and glovar.locks["ban"].acquire()

    try:
        if until_date:
            return kick_chat_member(client, gid, uid, until_date)

        kick_chat_member(client, gid, uid)
        sleep(3)
        unban_chat_member(client, gid, uid)

        result = True
    except Exception as e:
        logger.warning(f"Kick user error: {e}", exc_info=True)
    finally:
        lock and glovar.locks["ban"].release()

    return result


@threaded()
def restrict_user(client: Client, gid: int, uid: Union[int, str], until_date: int = 0) -> bool:
    # Restrict a user
    result = False

    try:
        result = restrict_chat_member(client, gid, uid, ChatPermissions(), until_date)
    except Exception as e:
        logger.warning(f"Restrict user error: {e}", exc_info=True)

    return result


def terminate_user(client: Client, message: Message, data: dict) -> bool:
    # Terminate user
    result = False

    try:
        # Basic data
        gid = message.chat.id
        user = message.from_user if message.new_chat_members else message.new_chat_members[0]
        uid = user.id
        key = data["key"]
        mid = data["mid"]
        word = data["word"]
        reply = data["reply"]
        actions = data["actions"]
        destruct = data["destruct"]
        forward = data["forward"]
        name = data["name"]
        now = get_now()

        # Check ignore status
        if is_class_d_user(uid) and gid not in glovar.ignore_ids["user"]:
            return False

        # Terminate
        action = get_action_text(actions)
        result = forward_evidence(
            client=client,
            message=message,
            user=user,
            level=action,
            rule=lang("rule_keyword"),
            keyword=word,
            forward=forward,
            name=name
        )

        if not result:
            return False

        # Send the debug message
        send_debug(
            client=client,
            chat=message.chat,
            action=action,
            uid=uid,
            em=result
        )

        # Delete the message
        if "delete" in actions:
            delete_message(client, gid, mid)
            actions.discard("delete")

        # Kick, ban, restrict the user
        if "kick" in actions:
            kick_user(client, gid, uid)
        elif "ban" in actions:
            ban_user(client, gid, uid)
        elif "restrict" in actions:
            restrict_user(client, gid, uid)
        elif any(a.startswith("ban-") or a.startswith("restrict-") for a in actions):
            time_user(client, gid, uid, now, actions)

        # Check reply action
        if "reply" not in actions:
            return False

        # Get the markup
        text, markup = get_text_and_markup_tip(gid, reply)
        text = get_text_user(text, user)
        text = text.replace("$destruct_time", str(destruct))

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
        logger.warning(f"Terminate user error: {e}", exc_info=True)

    return result


def time_user(client: Client, gid: int, uid: int, now: int, actions: set) -> bool:
    # Ban or restrict user with time
    result = False

    try:
        actions.discard("reply")
        action = list(actions)[0]
        time = get_int(action.split("-")[1])

        if action.startswith("ban"):
            ban_user(client, gid, uid, now + time)
        elif action.startswith("restrict"):
            restrict_user(client, gid, uid, now + time)

        result = True
    except Exception as e:
        logger.warning(f"Time user error: {e}", exc_info=True)

    return result
