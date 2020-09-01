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
from typing import Union

from pyrogram import Client
from pyrogram.types import ChatPermissions, Message

from .. import glovar
from .decorators import threaded
from .etc import get_now, random_str
from .file import save
from .telegram import kick_chat_member, restrict_chat_member, unban_chat_member

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
def ban_user(client: Client, gid: int, uid: Union[int, str], lock: bool = False) -> bool:
    # Ban a user
    result = False

    lock and glovar.locks["ban"].acquire()

    try:
        result = kick_chat_member(client, gid, uid)
    except Exception as e:
        logger.warning(f"Ban user error: {e}", exc_info=True)
    finally:
        lock and glovar.locks["ban"].release()

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
        uid = message.from_user.id
        key = data["key"]
        mid = data["mid"]
        reply = data["reply"]
        actions = data["actions"]
        destruct = data["destruct"]
        now = get_now()


    except Exception as e:
        logger.warning(f"Terminate user error: {e}", exc_info=True)

    return result
