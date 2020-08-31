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
from typing import List, Optional

from pyrogram import Client
from pyrogram.types import ChatMember, InlineKeyboardMarkup, InlineKeyboardButton

from .. import glovar
from .decorators import threaded
from .etc import code, lang, thread
from .file import save
from .ids import init_group_id
from .telegram import delete_messages, get_chat_member, leave_chat, send_message

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
