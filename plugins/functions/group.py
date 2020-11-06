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
from typing import List, Optional, Union

from pyrogram import Client
from pyrogram.types import Chat, ChatMember, InlineKeyboardMarkup, InlineKeyboardButton, Message

from .. import glovar
from .decorators import threaded
from .etc import code, lang, mention_id, mention_text, thread
from .file import save
from .ids import init_group_id
from .markup import get_text_and_markup
from .telegram import (delete_messages, get_chat, get_chat_member, leave_chat, pin_chat_message, send_message,
                       unpin_all_chat_messages, unpin_chat_message)

# Enable logging
logger = logging.getLogger(__name__)


@threaded()
def delete_message(client: Client, gid: int, mid: int) -> bool:
    # Delete a single message
    result = False

    try:
        if not gid or not mid:
            return True

        mids = [mid]
        result = delete_messages(client, gid, mids)
    except Exception as e:
        logger.warning(f"Delete message error: {e}", exc_info=True)

    return result


def get_group(client: Client, gid: int, cache: bool = True) -> Optional[Chat]:
    # Get the group
    result = None

    try:
        the_cache = glovar.chats.get(gid)

        if cache and the_cache:
            return the_cache

        result = get_chat(client, gid)

        if not result:
            return result

        glovar.chats[gid] = result
    except Exception as e:
        logger.warning(f"Get group error: {e}", exc_info=True)

    return result


def get_member(client: Client, gid: int, uid: int, cache: bool = True) -> Optional[ChatMember]:
    # Get a member in the group
    result = None

    try:
        if not init_group_id(gid):
            return None

        the_cache = glovar.members[gid].get(uid)

        if cache and the_cache:
            return the_cache

        result = get_chat_member(client, gid, uid)

        if not result:
            return result

        glovar.members[gid][uid] = result
    except Exception as e:
        logger.warning(f"Get member error: {e}", exc_info=True)

    return result


def get_pinned(client: Client, gid: int, cache: bool = True) -> Optional[Message]:
    # Get group's pinned message
    result = None

    try:
        group = get_group(client, gid, cache)

        if not group or not group.pinned_message:
            return None

        result = group.pinned_message
    except Exception as e:
        logger.warning(f"Get pinned error: {e}", exc_info=True)

    return result


def leave_group(client: Client, gid: int, reason: str = "") -> bool:
    # Leave a group, clear it's data
    result = False

    try:
        glovar.left_group_ids.add(gid)
        save("left_group_ids")
        leave_reason(client, gid, reason)
        thread(leave_chat, (client, gid))

        glovar.lack_group_ids.discard(gid)
        save("lack_group_ids")

        glovar.admin_ids.pop(gid, set())
        save("admin_ids")

        glovar.flooded_ids.discard(gid)
        save("flooded_ids")

        glovar.member_ids.pop(gid, set())
        save("member_ids")

        glovar.message_ids.pop(gid, {})
        save("message_ids")

        glovar.pinned_ids.pop(gid, 0)
        save("pinned_ids")

        glovar.trust_ids.pop(gid, set())
        save("trust_ids")

        glovar.channels.pop(gid, {})
        save("channels")

        glovar.configs.pop(gid, {})
        save("configs")

        glovar.keywords.pop(gid, {})
        save("keywords")

        glovar.ots.pop(gid, {})
        save("ots")

        glovar.rms.pop(gid, {})
        save("rms")

        glovar.welcomes.pop(gid, {})
        save("welcomes")

        glovar.chats.pop(gid, None)
        glovar.declared_message_ids.pop(gid, set())
        glovar.keyworded_ids.pop(gid, {})
        glovar.members.pop(gid, {})
        glovar.welcomed_ids.pop(gid, set())

        result = True
    except Exception as e:
        logger.warning(f"Leave group error: {e}", exc_info=True)

    return result


def leave_reason(client: Client, gid: int, reason: str = "") -> bool:
    # Send leave reason
    result = False

    try:
        if not reason:
            return False

        text = (f"{lang('action')}{lang('colon')}{code(lang('leave_group'))}\n"
                f"{lang('reason')}{lang('colon')}{code(glovar.leave_reason)}\n")
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=glovar.leave_button,
                        url=glovar.leave_link
                    )
                ]
            ]
        )
        result = send_message(client, gid, text, None, markup)
    except Exception as e:
        logger.warning(f"Leave reason error: {e}", exc_info=True)

    return result


def leave_unauthorized(client: Client, message: Message, text: str) -> bool:
    # Leave unauthorized group
    result = False

    try:
        gid = message.chat.id
        inviter = message.from_user

        if gid in glovar.left_group_ids:
            return leave_group(client, gid)

        leave_group(client, gid, glovar.leave_reason)

        text += (f"{lang('status')}{lang('colon')}{code(lang('status_left'))}\n"
                 f"{lang('reason')}{lang('colon')}{code(lang('reason_unauthorized'))}\n")

        if message.from_user.username:
            text += f"{lang('inviter')}{lang('colon')}{mention_id(inviter.id)}\n"
        else:
            text += f"{lang('inviter')}{lang('colon')}{code(inviter.id)}\n"

        return thread(send_message, (client, glovar.debug_channel_id, text))
    except Exception as e:
        logger.warning(f"Leave unauthorized error: {e}", exc_info=True)

    return result


@threaded()
def join_hint(client: Client, gid: int) -> bool:
    # Send join hint
    result = False

    try:
        if glovar.aio and glovar.sender != "TIP":
            return False

        text, markup = get_text_and_markup(glovar.join_text)

        if not text:
            return False

        text += "".join(mention_text("\U00002060", aid) for aid in glovar.admin_ids[gid])
        send_message(client, gid, text, None, markup)
    except Exception as e:
        logger.warning(f"Join hint error: {e}", exc_info=True)

    return result


def pin_cancel(client: Client, gid: int, hid: str, mid: int = 0) -> Union[bool, int]:
    # Unpin all the pinned messages
    result = False

    try:
        # Get chat
        chat = get_chat(client, gid)

        # Check if current pinned message is the held message
        if chat and chat.pinned_message and chat.pinned_message.message_id == mid:
            return mid

        # Check if there is no pinned message
        if not chat or not chat.pinned_message:
            return True

        # Record current pinned message
        oid = chat.pinned_message.message_id

        # Avoid flooding
        sleep(1)

        # Check hid
        if glovar.hold_ids.get(gid, "") != hid:
            return False

        # Unpin current pinned message
        r = unpin_chat_message(client, gid, chat.pinned_message.message_id)
        # r = unpin_all_chat_messages(client, gid)

        if not r:
            return False

        # Avoid flooding
        sleep(1)

        # Check hid
        if glovar.hold_ids.get(gid, "") != hid:
            return False

        # # Get chat
        # chat = get_chat(client, gid)
        #
        # # Check if current pinned message is the held message
        # if chat and chat.pinned_message and chat.pinned_message.message_id == mid:
        #     return mid
        #
        # # Check if there is no pinned message
        # if not chat or not chat.pinned_message:
        #     return True
        #
        # # Record current pinned message
        # nid = chat.pinned_message.message_id
        #
        # # Check the pinned message
        # if oid == nid:
        #     return True
        #
        # # Avoid flooding
        # sleep(1)
        #
        # # Check hid
        # if glovar.hold_ids.get(gid, "") != hid:
        #     return False

        # Try to unpin again
        return pin_cancel(client, gid, hid, mid)
    except Exception as e:
        logger.warning(f"Pin cancel error: {e}", exc_info=True)

    return result


def pin_hold(client: Client, gid: int, mid: int, hid: str) -> bool:
    # Hold the pinned message
    result = False

    try:
        # Check hid
        if glovar.hold_ids.get(gid, "") != hid:
            return False

        # Try to unpin the current pinned message
        pid = pin_cancel(client, gid, hid, mid)

        if pid == mid:
            return True

        # Check hid
        if glovar.hold_ids.get(gid, "") != hid:
            return False

        # Pin old message
        result = pin_chat_message(client, gid, mid)
    except Exception as e:
        logger.warning(f"Pin hold error: {e}", exc_info=True)

    return result


def save_admins(gid: int, admin_members: List[ChatMember]) -> bool:
    # Save the group's admin list
    result = False

    try:
        # Admin list
        glovar.admin_ids[gid] = {admin.user.id for admin in admin_members
                                 if (((not admin.user.is_bot and not admin.user.is_deleted)
                                      and admin.can_delete_messages
                                      and admin.can_restrict_members)
                                     or admin.status == "creator"
                                     or admin.user.id in glovar.bot_ids)}
        save("admin_ids")

        # Trust list
        glovar.trust_ids[gid] = {admin.user.id for admin in admin_members
                                 if ((not admin.user.is_bot and not admin.user.is_deleted)
                                     or admin.user.id in glovar.bot_ids)}
        save("trust_ids")

        result = True
    except Exception as e:
        logger.warning(f"Save admins error: {e}", exc_info=True)

    return result
