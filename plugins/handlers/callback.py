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
from json import loads

from pyrogram import Client
from pyrogram.types import CallbackQuery

from ..functions.etc import thread
from ..functions.filters import authorized_group, test_group
from ..functions.telegram import answer_callback
from ..functions.tip import tip_saved

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_callback_query(~test_group & authorized_group)
def send_saved(client: Client, callback_query: CallbackQuery) -> bool:
    # Answer the saved query
    result = False

    try:
        # Check the message
        if not callback_query.message or not callback_query.message.date:
            return False

        # Basic data
        gid = callback_query.message.chat.id
        user = callback_query.from_user
        callback_data = loads(callback_query.data)
        action = callback_data["a"]
        action_type = callback_data["t"]
        data = callback_data["d"]

        # Check the action
        if action != "send" or action_type != "saved":
            return False

        # Send saved message
        tip_saved(client, gid, user, data)

        # Answer the callback
        thread(answer_callback, (client, callback_query.id, ""))

        result = True
    except Exception as e:
        logger.warning(f"Send saved error: {e}", exc_info=True)

    return result
