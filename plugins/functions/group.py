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
        captcha_text = (lambda x: lang("enabled") if x else lang("disabled"))(config.get("captcha"))
        clean_text = (lambda x: lang("enabled") if x else lang("disabled"))(config.get("clean"))
        resend_text = (lambda x: lang("enabled") if x else lang("disabled"))(config.get("resend"))
        channel_text = (lambda x: config["channel"] if x else lang("disabled"))(config.get("channel"))
        result += (f"{lang('config')}{lang('colon')}{code(default_text)}\n"
                   f"{lang('captcha')}{lang('colon')}{code(captcha_text)}\n"
                   f"{lang('clean')}{lang('colon')}{code(clean_text)}\n"
                   f"{lang('resend')}{lang('colon')}{code(resend_text)}\n"
                   f"{lang('channel')}{lang('colon')}{code(channel_text)}\n")

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

        glovar.admin_ids.pop(gid, set())
        save("admin_ids")

        glovar.message_ids.pop(gid, {})
        save("message_ids")

        glovar.configs.pop(gid, {})
        save("configs")

        return True
    except Exception as e:
        logger.warning(f"Leave group error: {e}", exc_info=True)

    return False
