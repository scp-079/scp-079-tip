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
from typing import Optional

from pyrogram import ChatMember, Client

from .. import glovar
from .etc import code, lang, thread
from .file import save
from .ids import init_group_id
from .telegram import delete_messages, get_chat_member, leave_chat

# Enable logging
logger = logging.getLogger(__name__)


def delete_message(client: Client, gid: int, mid: int) -> bool:
    # Delete a single message
    try:
        if not gid or not mid:
            return True

        mids = [mid]
        thread(delete_messages, (client, gid, mids))

        return True
    except Exception as e:
        logger.warning(f"Delete message error: {e}", exc_info=True)

    return False


def get_config_text(config: dict) -> str:
    # Get config text
    result = ""
    try:
        # Basic
        default_text = (lambda x: lang("default") if x else lang("custom"))(config.get("default"))
        result += f"{lang('config')}{lang('colon')}{code(default_text)}\n"

        # CAPTCHA, alone, clean, resend
        for the_type in ["captcha", "alone", "clean", "resend"]:
            the_text = (lambda x: lang("enabled") if x else lang("disabled"))(config.get(the_type))
            result += f"{lang(the_type)}{lang('colon')}{code(the_text)}\n"

        # Channel, hold
        for the_type in ["channel", "hold"]:
            channel_text = (lambda x: config[the_type] if x else lang("disabled"))(config.get(the_type))
            result += f"{lang(the_type)}{lang('colon')}{code(channel_text)}\n"

        # Others
        for the_type in ["keyword", "ot", "rm", "welcome"]:
            the_text = (lambda x: lang("enabled") if x else lang("disabled"))(config.get(the_type))
            result += f"{lang(the_type)}{lang('colon')}{code(the_text)}\n"
    except Exception as e:
        logger.warning(f"Get config text error: {e}", exc_info=True)

    return result


def get_member(client: Client, gid: int, uid: int, cache: bool = True) -> Optional[ChatMember]:
    # Get a member in the group
    result = None
    try:
        if not init_group_id(gid):
            return None

        the_cache = glovar.members[gid].get(uid)

        if the_cache:
            result = the_cache
        else:
            result = get_chat_member(client, gid, uid)

        if cache and result:
            glovar.members[gid][uid] = result
    except Exception as e:
        logger.warning(f"Get member error: {e}", exc_info=True)

    return result


def leave_group(client: Client, gid: int) -> bool:
    # Leave a group, clear it's data
    try:
        glovar.left_group_ids.add(gid)
        save("left_group_ids")
        thread(leave_chat, (client, gid))

        glovar.lack_group_ids.discard(gid)
        save("lack_group_ids")

        glovar.admin_ids.pop(gid, set())
        save("admin_ids")

        glovar.message_ids.pop(gid, {})
        save("message_ids")

        glovar.trust_ids.pop(gid, set())
        save("trust_ids")

        glovar.configs.pop(gid, {})
        save("configs")

        glovar.declared_message_ids.pop(gid, set())
        glovar.members.pop(gid, {})
        glovar.keyworded_ids.pop(gid, {})
        glovar.welcomed_ids.pop(gid, set())

        return True
    except Exception as e:
        logger.warning(f"Leave group error: {e}", exc_info=True)

    return False
