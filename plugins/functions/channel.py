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
from json import dumps
from typing import List, Optional, Union

from pyrogram import Client
from pyrogram.types import Chat, Message, User

from .. import glovar
from .decorators import retry, threaded
from .etc import code, code_block, general_link, get_forward_name, get_full_name, lang, thread
from .file import crypt_file, data_to_file, delete_file, get_new_path, save
from .telegram import forward_messages, get_group_info, send_document, send_message

# Enable logging
logger = logging.getLogger(__name__)


def declare_message(client: Client, gid: int, mid: int) -> bool:
    # Declare a message
    result = False

    try:
        glovar.declared_message_ids[gid].add(mid)
        result = share_data(
            client=client,
            receivers=glovar.receivers["declare"],
            action="update",
            action_type="declare",
            data={
                "group_id": gid,
                "message_id": mid
            }
        )
    except Exception as e:
        logger.warning(f"Declare message error: {e}", exc_info=True)

    return result


def exchange_to_hide(client: Client) -> bool:
    # Let other bots exchange data in the hide channel instead
    result = False

    try:
        # Transfer the channel
        glovar.should_hide = True
        share_data(
            client=client,
            receivers=["EMERGENCY"],
            action="backup",
            action_type="hide",
            data=True
        )

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{code(glovar.sender)}\n"
                f"{lang('issue')}{lang('colon')}{code(lang('exchange_invalid'))}\n"
                f"{lang('auto_fix')}{lang('colon')}{code(lang('protocol_1'))}\n")
        thread(send_message, (client, glovar.critical_channel_id, text))

        result = True
    except Exception as e:
        logger.warning(f"Exchange to hide error: {e}", exc_info=True)

    return result


def format_data(sender: str, receivers: List[str], action: str, action_type: str,
                data: Union[bool, dict, int, str] = None) -> str:
    # Get exchange string
    result = ""

    try:
        data = {
            "from": sender,
            "to": receivers,
            "action": action,
            "type": action_type,
            "data": data
        }
        result = code_block(dumps(data, indent=4))
    except Exception as e:
        logger.warning(f"Format data error: {e}", exc_info=True)

    return result


@retry
def forward_evidence(client: Client, message: Message, user: User, level: str, rule: str,
                     keyword: str, forward: bool = False, name: bool = False,
                     more: str = None) -> Optional[Union[bool, Message]]:
    # Forward the message to the logging channel as evidence
    result = None

    try:
        # Basic information
        uid = user.id
        text = (f"{lang('project')}{lang('colon')}{code(glovar.sender)}\n"
                f"{lang('user_id')}{lang('colon')}{code(uid)}\n"
                f"{lang('level')}{lang('colon')}{code(level)}\n"
                f"{lang('rule')}{lang('colon')}{code(rule)}\n")
        text += f"{lang('keyword')}{lang('colon')}{code(keyword)}\n"

        # Additional information
        if message.game:
            text += (f"{lang('message_type')}{lang('colon')}{code(lang('gam'))}\n"
                     f"{lang('message_game')}{lang('colon')}{code(message.game.short_name)}\n")
        elif message.service:
            text += f"{lang('message_type')}{lang('colon')}{code(lang('ser'))}\n"

        # Name information
        if forward and name:
            text += f"{lang('from_name')}{lang('colon')}{code(get_forward_name(message))}\n"
        elif name:
            text += f"{lang('user_name')}{lang('colon')}{code(get_full_name(user))}\n"

        # Extra information
        if message.contact or message.location or message.venue or message.video_note or message.voice:
            text += f"{lang('more')}{lang('colon')}{code(lang('privacy'))}\n"
        elif message.game or message.service:
            text += f"{lang('more')}{lang('colon')}{code(lang('cannot_forward'))}\n"
        elif more:
            text += f"{lang('more')}{lang('colon')}{code(more)}\n"

        # DO NOT try to forward these types of message
        if (message.contact
                or message.location
                or message.venue
                or message.video_note
                or message.voice
                or message.game
                or message.service):
            result = send_message(client, glovar.logging_channel_id, text)
            return result

        # Forward the evidence
        result = forward_messages(
            client=client,
            cid=glovar.tip_channel_id,
            fid=message.chat.id,
            mids=[message.message_id]
        )

        # Attach information
        result = result.message_id
        result = send_message(client, glovar.tip_channel_id, text, result)
    except Exception as e:
        logger.warning(f"Forward evidence error: {e}", exc_info=True)

    return result


def get_debug_text(client: Client, context: Union[int, Chat, List[int]]) -> str:
    # Get a debug message text prefix
    result = ""

    try:
        # Prefix
        result = f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"

        # List of group ids
        gids = context if isinstance(context, list) else []

        for group_id in gids:
            group_name, group_link = get_group_info(client, group_id)
            result += (f"{lang('group_name')}{lang('colon')}{general_link(group_name, group_link)}\n"
                       f"{lang('group_id')}{lang('colon')}{code(group_id)}\n")

        if gids:
            return result

        # One group
        if isinstance(context, int):
            group_id = context
        else:
            group_id = context.id

        # Generate the group info text
        group_name, group_link = get_group_info(client, context)
        result += (f"{lang('group_name')}{lang('colon')}{general_link(group_name, group_link)}\n"
                   f"{lang('group_id')}{lang('colon')}{code(group_id)}\n")
    except Exception as e:
        logger.warning(f"Get debug text error: {e}", exc_info=True)

    return result


@threaded()
def send_debug(client: Client, chat: Chat, action: str,
               uid: int, aid: int = 0,
               em: Message = 0,
               config_type: str = "", more: str = "") -> bool:
    # Send the debug message
    result = False

    try:
        if not chat:
            return False

        text = get_debug_text(client, chat)

        if uid:
            text += f"{lang('user_id')}{lang('colon')}{code(uid)}\n"

        text += f"{lang('action')}{lang('colon')}{code(action)}\n"

        if aid:
            text += f"{lang('admin_group')}{lang('colon')}{code(aid)}\n"

        if em:
            text += f"{lang('triggered_by')}{lang('colon')}{general_link(em.message_id, em.link)}\n"

        if config_type:
            text += f"{lang('type')}{lang('colon')}{code(config_type)}\n"

        if more:
            text += f"{lang('more')}{lang('colon')}{code(more)}\n"

        result = bool(send_message(client, glovar.debug_channel_id, text))
    except Exception as e:
        logger.warning(f"Send debug error: {e}", exc_info=True)

    return result


@threaded()
def share_data(client: Client, receivers: List[str], action: str, action_type: str,
               data: Union[bool, dict, int, str] = None, file: str = None, encrypt: bool = True) -> bool:
    # Use this function to share data in the channel
    result = False

    try:
        if glovar.sender in receivers:
            receivers.remove(glovar.sender)

        if not receivers:
            return False

        if glovar.should_hide:
            channel_id = glovar.hide_channel_id
        else:
            channel_id = glovar.exchange_channel_id

        # Plain text
        if not file:
            text = format_data(
                sender=glovar.sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )
            result = send_message(client, channel_id, text)
            return ((result is not False or glovar.should_hide)
                    or share_data_failed(client, receivers, action, action_type, data, file, encrypt))

        # Share with a file
        text = format_data(
            sender=glovar.sender,
            receivers=receivers,
            action=action,
            action_type=action_type,
            data=data
        )

        if encrypt:
            # Encrypt the file, save to the tmp directory
            file_path = get_new_path()
            crypt_file("encrypt", file, file_path)
        else:
            # Send directly
            file_path = file

        result = send_document(client, channel_id, file_path, None, text)

        if not result:
            return ((result is not False or glovar.should_hide)
                    or share_data_failed(client, receivers, action, action_type, data, file, encrypt))

        # Delete the tmp file
        for f in {file, file_path}:
            f.startswith("tmp/") and thread(delete_file, (f,))

        result = bool(result)
    except Exception as e:
        logger.warning(f"Share data error: {e}", exc_info=True)

    return result


@threaded()
def share_data_failed(client: Client, receivers: List[str], action: str, action_type: str,
                      data: Union[bool, dict, int, str] = None, file: str = None, encrypt: bool = True) -> bool:
    # Sharing data failed, use the exchange channel instead
    result = False

    try:
        exchange_to_hide(client)
        result = share_data(
            client=client,
            receivers=receivers,
            action=action,
            action_type=action_type,
            data=data,
            file=file,
            encrypt=encrypt
        )
    except Exception as e:
        logger.warning(f"Share data failed error: {e}", exc_info=True)

    return result


def share_regex_count(client: Client, word_type: str) -> bool:
    # Use this function to share regex count to REGEX
    result = False

    try:
        if not glovar.regex.get(word_type):
            return False

        if not eval(f"glovar.{word_type}_words"):
            return False

        file = data_to_file(eval(f"glovar.{word_type}_words"))
        result = share_data(
            client=client,
            receivers=["REGEX"],
            action="regex",
            action_type="count",
            data=f"{word_type}_words",
            file=file
        )
    except Exception as e:
        logger.warning(f"Share regex update error: {e}", exc_info=True)

    return result


def share_regex_remove(client: Client, word_type: str, word: str) -> bool:
    # Use this function to share regex remove request to REGEX
    result = False

    try:
        eval(f"glovar.{word_type}_words").pop(word, 0)
        save(f"{word_type}_words")
        file = data_to_file(word)
        result = share_data(
            client=client,
            receivers=["REGEX"],
            action="regex",
            action_type="remove",
            data=f"{word_type}_words",
            file=file
        )
    except Exception as e:
        logger.warning(f"Share regex remove error: {e}", exc_info=True)

    return result
