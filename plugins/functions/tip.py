# SCP-079-TIP - Here's a tip
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
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

from pyrogram import Client, InlineKeyboardButton, InlineKeyboardMarkup

from .. import glovar
from .etc import get_now
from .file import save
from .group import delete_message
from .telegram import edit_message_text, export_chat_invite_link, send_message


# Enable logging
logger = logging.getLogger(__name__)


def get_keywords(text: str) -> dict:
    # Get keywords
    try:
        # Check the text
        if not text:
            return {}

        text_list = [t for t in text.split("\n+++") if t]

        if not text_list or len(text_list) % 2 != 0:
            return {}

        # Get keyword_list
        keyword_list = [t.strip() for t in text_list[0::2]]
        reply_list = [t.strip() for t in text_list[1::2]]

        # Get keyword dict
        keywords = {}

        for i in range(len(keyword_list)):
            keyword = keyword_list[i]
            reply = reply_list[i]

            k_list = [k.strip() for k in keyword.split("||") if k.strip()]

            for k in k_list:
                keywords[k] = reply
    except Exception as e:
        logger.warning(f"Get keywords error: {e}", exc_info=True)

    return {}


def get_invite_link(client: Client, the_type: str, gid: int) -> bool:
    # Get a new invite link
    glovar.locks["channel"].acquire()
    try:
        # Basic data
        now = get_now()

        # Read the config
        cid = glovar.configs[gid]["channel"]
        channel_text = glovar.configs[gid]["channel_text"]
        channel_button = glovar.configs[gid]["channel_button"]
        mid, time = glovar.message_ids[gid]["channel"]

        # Check the config
        if not cid:
            return False

        # Generate link
        link = export_chat_invite_link(client, gid)

        # Check the link
        if link is False:
            glovar.configs[gid]["channel"] = 0
            save("configs")
            glovar.message_ids[gid]["channel"] = (0, 0)
            save("message_ids")
            delete_message(client, cid, mid)
            return False
        elif not link:
            return False

        # Update the link
        glovar.configs[gid]["channel_link"] = link
        save("configs")

        # Generate text and markup
        text = channel_text
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=channel_button,
                        url=link
                    )
                ]
            ]
        )

        # Edit message
        if the_type == "edit" and mid:
            result = edit_message_text(client, cid, mid, text, markup)
            if result:
                glovar.message_ids[gid]["channel"] = (mid, now)
                save("message_ids")
                return True

        # Send new message
        result = send_message(client, cid, text, None, markup)
        if result:
            glovar.message_ids[gid]["channel"] = (result.message_id, now)
            save("message_ids")
            mid and delete_message(client, cid, mid)
            return True
    except Exception as e:
        logger.warning(f"New invite link error: {e}", exc_info=True)
    finally:
        glovar.locks["channel"].release()

    return False
