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
from typing import Generator, Iterable, List, Optional, Union

from pyrogram import Client
from pyrogram.errors import (ButtonDataInvalid, ButtonUrlInvalid, ChatAdminRequired, ChatNotModified, ChannelInvalid,
                             ChannelPrivate, FloodWait, MessageDeleteForbidden, MessageIdInvalid, MessageNotModified,
                             PeerIdInvalid, QueryIdInvalid, UsernameInvalid, UsernameNotOccupied, UserNotParticipant)
from pyrogram.raw.base import InputChannel, InputUser, InputPeer
from pyrogram.raw.functions.users import GetFullUser
from pyrogram.raw.types import UserFull
from pyrogram.types import (Chat, ChatMember, ChatPermissions, ChatPreview, InlineKeyboardMarkup, Message,
                            ReplyKeyboardMarkup, User)

from .decorators import threaded, retry
from .etc import delay, wait_flood
from .. import glovar

# Enable logging
logger = logging.getLogger(__name__)


@retry
def answer_callback(client: Client, callback_query_id: str, text: str, show_alert: bool = False) -> Optional[bool]:
    # Answer the callback
    result = None

    try:
        result = client.answer_callback_query(
            callback_query_id=callback_query_id,
            text=text,
            show_alert=show_alert
        )
    except FloodWait as e:
        logger.warning(f"Answer callback to {callback_query_id} - Sleep for {e.x} second(s)")
        raise e
    except QueryIdInvalid:
        return False
    except Exception as e:
        logger.warning(f"Answer query to {callback_query_id} error: {e}", exc_info=True)

    return result


def delete_messages(client: Client, cid: int, mids: Iterable[int]) -> Optional[bool]:
    # Delete some messages
    result = None

    try:
        mids = list(mids)

        if len(mids) <= 100:
            return delete_messages_100(client, cid, mids)

        mids_list = [mids[i:i + 100] for i in range(0, len(mids), 100)]
        result = bool([delete_messages_100(client, cid, mids) for mids in mids_list])
    except Exception as e:
        logger.warning(f"Delete messages in {cid} error: {e}", exc_info=True)

    return result


@retry
def delete_messages_100(client: Client, cid: int, mids: Iterable[int]) -> Optional[bool]:
    # Delete some messages
    result = None

    try:
        mids = list(mids)
        result = client.delete_messages(chat_id=cid, message_ids=mids)
    except FloodWait as e:
        logger.warning(f"Delete message in {cid} - Sleep for {e.x} second(s)")
        raise e
    except MessageDeleteForbidden:
        return False
    except Exception as e:
        logger.warning(f"Delete messages in {cid} error: {e}", exc_info=True)

    return result


@retry
def download_media(client: Client, file_id: str, file_ref: str, file_path: str) -> Optional[str]:
    # Download a media file
    result = None

    try:
        result = client.download_media(message=file_id, file_ref=file_ref, file_name=file_path)
    except FloodWait as e:
        logger.warning(f"Download media {file_id} - Sleep for {e.x} second(s)")
        raise e
    except Exception as e:
        logger.warning(f"Download media {file_id} to {file_path} error: {e}", exc_info=True)

    return result


@retry
def edit_message_text(client: Client, cid: int, mid: int, text: str,
                      markup: InlineKeyboardMarkup = None) -> Union[bool, Message, None]:
    # Edit the message's text
    result = None

    try:
        if not text.strip():
            return None

        result = client.edit_message_text(
            chat_id=cid,
            message_id=mid,
            text=text,
            parse_mode="html",
            disable_web_page_preview=True,
            reply_markup=markup
        )
    except FloodWait as e:
        logger.warning(f"Edit message {mid} text in {cid} - Sleep for {e.x} second(s)")
        raise e
    except (ButtonDataInvalid, ButtonUrlInvalid):
        logger.warning(f"Edit message {mid} text in {cid} - invalid markup: {markup}")
    except MessageIdInvalid:
        logger.warning(f"Edit message {mid} text in {cid} - invalid mid")
        return None
    except (ChannelInvalid, ChannelPrivate, ChatAdminRequired, PeerIdInvalid, MessageNotModified):
        return False
    except Exception as e:
        logger.warning(f"Edit message {mid} in {cid} error: {e}", exc_info=True)

    return result


@retry
def export_chat_invite_link(client: Client, cid: int) -> Union[bool, str, None]:
    # Generate a new link for a chat
    result = None

    try:
        result = client.export_chat_invite_link(chat_id=cid)
    except FloodWait as e:
        logger.warning(f"Export chat invite link in {cid} - Sleep for {e.x} second(s)")
        raise e
    except (ChannelInvalid, ChannelPrivate, ChatAdminRequired, PeerIdInvalid) as e:
        logger.warning(f"Export chat invite link in {cid} error: {e}")
        return ""
    except Exception as e:
        logger.warning(f"Export chat invite link in {cid} error: {e}", exc_info=True)

    return result


@retry
def forward_messages(client: Client, cid: int, fid: int, mids: Union[int, Iterable[int]],
                     as_copy: bool = False) -> Union[bool, Message, List[Message], None]:
    # Forward messages of any kind
    result = None

    try:
        result = client.forward_messages(
            chat_id=cid,
            from_chat_id=fid,
            message_ids=mids,
            disable_notification=True,
            as_copy=as_copy
        )
    except FloodWait as e:
        logger.warning(f"Forward message from {fid} to {cid} - Sleep for {e.x} second(s)")
        raise e
    except (ChannelInvalid, ChannelPrivate, ChatAdminRequired, MessageIdInvalid, PeerIdInvalid):
        return False
    except Exception as e:
        logger.warning(f"Forward messages error: {e}", exc_info=True)

    return result


@retry
def get_admins(client: Client, cid: int) -> Union[bool, List[ChatMember], None]:
    # Get a group's admins
    result = None

    try:
        chat = get_chat(client, cid)

        if isinstance(chat, Chat) and not chat.members_count:
            return False

        result = client.get_chat_members(chat_id=cid, filter="administrators")
    except FloodWait as e:
        logger.warning(f"Get admins in {cid} - Sleep for {e.x} second(s)")
        raise e
    except AttributeError as e:
        if "BadSeverSalt" in str(e):
            return None
        else:
            return False
    except (ChannelInvalid, ChannelPrivate, PeerIdInvalid):
        return False
    except Exception as e:
        logger.warning(f"Get admins in {cid} error: {e}", exc_info=True)

    return result


@retry
def get_chat(client: Client, cid: Union[int, str]) -> Union[Chat, ChatPreview, None]:
    # Get a chat
    result = None

    try:
        result = client.get_chat(chat_id=cid)
    except FloodWait as e:
        logger.warning(f"Get chat {cid} - Sleep for {e.x} second(s)")
        raise e
    except (ChannelInvalid, ChannelPrivate, PeerIdInvalid):
        return None
    except Exception as e:
        logger.warning(f"Get chat {cid} error: {e}", exc_info=True)

    return result


@retry
def get_chat_member(client: Client, cid: int, uid: int) -> Union[bool, ChatMember, None]:
    # Get information about one member of a chat
    result = None

    try:
        result = client.get_chat_member(chat_id=cid, user_id=uid)
    except FloodWait as e:
        logger.warning(f"Get chat member {uid} in {cid} - Sleep for {e.x} second(s)")
        raise e
    except (ChannelInvalid, ChannelPrivate, PeerIdInvalid, UserNotParticipant):
        result = False
    except Exception as e:
        logger.warning(f"Get chat member {uid} in {cid} error: {e}", exc_info=True)

    return result


def get_group_info(client: Client, chat: Union[int, Chat], cache: bool = True) -> (str, str):
    # Get a group's name and link
    group_name = "Unknown Group"
    group_link = glovar.default_group_link

    try:
        if isinstance(chat, int):
            the_cache = glovar.chats.get(chat)

            if cache and the_cache:
                result = the_cache
            else:
                result = get_chat(client, chat)

            if result:
                glovar.chats[chat] = result

            chat = result

        if not chat:
            return group_name, group_link

        if chat.title:
            group_name = chat.title

        if chat.username:
            group_link = "https://t.me/" + chat.username
    except Exception as e:
        logger.warning(f"Get group {chat} info error: {e}", exc_info=True)

    return group_name, group_link


@retry
def get_me(client: Client) -> Optional[User]:
    # Get myself
    result = None

    try:
        result = client.get_me()
    except FloodWait as e:
        logger.warning(f"Get me - Sleep for {e.x} second(s)")
        raise e
    except Exception as e:
        logger.warning(f"Get me error: {e}", exc_info=True)

    return result


@retry
def get_members(client: Client, cid: int, query: str = "all") -> Union[bool, Generator[ChatMember, None, None], None]:
    # Get a members generator of a chat
    result = None

    try:
        result = client.iter_chat_members(chat_id=cid, filter=query)
    except FloodWait as e:
        logger.warning(f"Get members in {cid} - Sleep for {e.x} second(s)")
        raise e
    except (AttributeError, ChannelInvalid, ChannelPrivate, PeerIdInvalid):
        return False
    except Exception as e:
        logger.warning(f"Get members in {cid} error: {e}", exc_info=True)

    return result


@retry
def get_messages(client: Client, cid: int, mids: Union[int, Iterable[int]]) -> Union[Message, List[Message], None]:
    # Get some messages
    result = None

    try:
        result = client.get_messages(chat_id=cid, message_ids=mids)
    except FloodWait as e:
        raise e
    except (ChannelInvalid, ChannelPrivate, MessageIdInvalid, PeerIdInvalid):
        return None
    except Exception as e:
        logger.warning(f"Get messages {mids} in {cid} error: {e}", exc_info=True)

    return result


def get_start(client: Client, para: str) -> str:
    # Get start link with parameter
    result = ""

    try:
        me = get_me(client)

        if not me or not me.username:
            return ""

        result = f"https://t.me/{me.username}?start={para}"
    except Exception as e:
        logger.warning(f"Get start error: {e}", exc_info=True)

    return result


@retry
def get_user_full(client: Client, uid: int) -> Optional[UserFull]:
    # Get a full user
    result = None

    try:
        user_id = resolve_peer(client, uid)

        if not user_id:
            return None

        result = client.send(GetFullUser(id=user_id))
    except FloodWait as e:
        logger.warning(f"Get user {uid} full - Sleep for {e.x} second(s)")
        raise e
    except Exception as e:
        logger.warning(f"Get user {uid} full error: {e}", exc_info=True)

    return result


def kick_chat_member(client: Client, cid: int, uid: Union[int, str],
                     until_date: int = 0) -> Union[bool, Message, None]:
    # Kick a chat member in a group
    result = None

    try:
        result = client.kick_chat_member(chat_id=cid, user_id=uid, until_date=until_date)
    except FloodWait as e:
        logger.warning(f"Kick chat member {uid} in {cid} - Sleep for {e.x} second(s)")

        if until_date:
            new_date = until_date + e.x
        else:
            new_date = 0

        wait_flood(e)

        return kick_chat_member(client, cid, uid, new_date)
    except PeerIdInvalid:
        return False
    except Exception as e:
        logger.warning(f"Kick chat member {uid} in {cid} error: {e}", exc_info=True)

    return result


@retry
def leave_chat(client: Client, cid: int, delete: bool = False) -> bool:
    # Leave a channel
    result = False

    try:
        result = client.leave_chat(chat_id=cid, delete=delete) or True
    except FloodWait as e:
        logger.warning(f"Leave chat {cid} - Sleep for {e.x} second(s)")
        raise e
    except (ChannelInvalid, ChannelPrivate, PeerIdInvalid):
        return False
    except Exception as e:
        logger.warning(f"Leave chat {cid} error: {e}", exc_info=True)

    return result


@retry
def pin_chat_message(client: Client, cid: int, mid: int) -> Optional[bool]:
    # Pin a message in a group, channel or your own chat
    result = None

    try:
        result = client.pin_chat_message(
            chat_id=cid,
            message_id=mid,
            disable_notification=True
        )
    except FloodWait as e:
        logger.warning(f"Pin chat message {mid} in {cid} - Sleep for {e.x} second(s)")
        raise e
    except (ChannelInvalid, ChannelPrivate, ChatAdminRequired, ChatNotModified, PeerIdInvalid):
        return False
    except Exception as e:
        logger.warning(f"Pin chat message error: {e}", exc_info=True)

    return result


@retry
def resolve_peer(client: Client, pid: Union[int, str]) -> Union[bool, InputChannel, InputPeer, InputUser, None]:
    # Get an input peer by id
    result = None

    try:
        result = client.resolve_peer(pid)
    except FloodWait as e:
        logger.warning(f"Resolve peer {pid} - Sleep for {e.x} second(s)")
        raise e
    except (PeerIdInvalid, UsernameInvalid, UsernameNotOccupied):
        return False
    except Exception as e:
        logger.warning(f"Resolve peer {pid} error: {e}", exc_info=True)

    return result


@retry
def restrict_chat_member(client: Client, cid: int, uid: int, permissions: ChatPermissions,
                         until_date: int = 0) -> Optional[Chat]:
    # Restrict a user in a supergroup
    result = None

    try:
        result = client.restrict_chat_member(
            chat_id=cid,
            user_id=uid,
            permissions=permissions,
            until_date=until_date
        )
    except FloodWait as e:
        logger.warning(f"Restrict chat member {uid} in {cid} - Sleep for {e.x} second(s)")

        if until_date:
            new_date = until_date + e.x
        else:
            new_date = 0

        wait_flood(e)

        return restrict_chat_member(client, cid, uid, permissions, new_date)
    except Exception as e:
        logger.warning(f"Restrict chat member {uid} in {cid} error: {e}", exc_info=True)

    return result


@retry
def send_document(client: Client, cid: int, document: str, file_ref: str = None, caption: str = "", mid: int = None,
                  markup: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup] = None) -> Union[bool, Message, None]:
    # Send a document to a chat
    result = None

    try:
        result = client.send_document(
            chat_id=cid,
            document=document,
            file_ref=file_ref,
            caption=caption,
            parse_mode="html",
            reply_to_message_id=mid,
            reply_markup=markup
        )
    except FloodWait as e:
        logger.warning(f"Send document {document} to {cid} - Sleep for {e.x} second(s)")
        raise e
    except (ButtonDataInvalid, ButtonUrlInvalid):
        logger.warning(f"Send document {document} to {cid} - invalid markup: {markup}")
    except (ChannelInvalid, ChannelPrivate, ChatAdminRequired, PeerIdInvalid):
        return False
    except Exception as e:
        logger.warning(f"Send document {document} to {cid} error: {e}", exc_info=True)

    return result


@retry
def send_message(client: Client, cid: int, text: str, mid: int = None,
                 markup: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup] = None) -> Union[bool, Message, None]:
    # Send a message to a chat
    result = None

    try:
        if not text.strip():
            return None

        result = client.send_message(
            chat_id=cid,
            text=text,
            parse_mode="html",
            disable_web_page_preview=True,
            reply_to_message_id=mid,
            reply_markup=markup
        )
    except FloodWait as e:
        logger.warning(f"Send message to {cid} - Sleep for {e.x} second(s)")
        raise e
    except (ButtonDataInvalid, ButtonUrlInvalid):
        logger.warning(f"Send message to {cid} - invalid markup: {markup}")
    except (ChannelInvalid, ChannelPrivate, ChatAdminRequired, PeerIdInvalid):
        return False
    except Exception as e:
        logger.warning(f"Send message to {cid} error: {e}", exc_info=True)

    return result


@retry
def send_photo(client: Client, cid: int, photo: str, file_ref: str = None, caption: str = "", mid: int = None,
               markup: Union[InlineKeyboardMarkup, ReplyKeyboardMarkup] = None) -> Union[bool, Message, None]:
    # Send a photo to a chat
    result = None

    try:
        if not photo.strip():
            return None

        result = client.send_photo(
            chat_id=cid,
            photo=photo,
            file_ref=file_ref,
            caption=caption,
            parse_mode="html",
            reply_to_message_id=mid,
            reply_markup=markup
        )
    except FloodWait as e:
        logger.warning(f"Send photo {photo} to {cid} - Sleep for {e.x} second(s)")
        raise e
    except (ButtonDataInvalid, ButtonUrlInvalid):
        logger.warning(f"Send photo {photo} to {cid} - invalid markup: {markup}")
    except (ChannelInvalid, ChannelPrivate, ChatAdminRequired, PeerIdInvalid):
        return False
    except Exception as e:
        logger.warning(f"Send photo {photo} to {cid} error: {e}", exc_info=True)

    return result


@threaded()
def send_report_message(secs: int, client: Client, cid: int, text: str, mid: int = None,
                        markup: InlineKeyboardMarkup = None) -> Optional[bool]:
    # Send a message that will be auto deleted to a chat
    result = None

    try:
        result = send_message(
            client=client,
            cid=cid,
            text=text,
            mid=mid,
            markup=markup
        )

        if not result:
            return None

        mid = result.message_id
        mids = [mid]
        result = delay(secs, delete_messages, [client, cid, mids])
    except Exception as e:
        logger.warning(f"Send report message to {cid} error: {e}", exc_info=True)

    return result


@retry
def unban_chat_member(client: Client, cid: int, uid: Union[int, str]) -> Optional[bool]:
    # Unban a user in a group
    result = None

    try:
        result = client.unban_chat_member(chat_id=cid, user_id=uid)
    except FloodWait as e:
        logger.warning(f"Unban chat member {uid} in {cid} - Sleep for {e.x} second(s)")
        raise e
    except Exception as e:
        logger.warning(f"Unban chat member {uid} in {cid} error: {e}", exc_info=True)

    return result


@retry
def unpin_chat_message(client: Client, cid: int, mid: int) -> Optional[bool]:
    # Unpin a message in a group, channel or your own chat
    result = None

    try:
        # result = client.unpin_chat_message(
        #     chat_id=cid,
        #     message_id=mid
        # )
        result = client.unpin_chat_message(
            chat_id=cid
        )
    except FloodWait as e:
        logger.warning(f"Unpin chat message {mid} in {cid} - Sleep for {e.x} second(s)")
        raise e
    except (ChannelInvalid, ChannelPrivate, ChatAdminRequired, ChatNotModified, PeerIdInvalid):
        return False
    except Exception as e:
        logger.warning(f"Unpin chat message {mid} in {cid} error: {e}", exc_info=True)

    return result


@retry
def unpin_all_chat_messages(client: Client, cid: int) -> Optional[bool]:
    # Unpin all messages in a group
    result = None

    try:
        from subprocess import run
        url = f"https://api.telegram.org/bot{glovar.token}/unpinAllChatMessages?chat_id={cid}"
        run(f"""curl -g '{url}'""", shell=True)
        result = True
    except FloodWait as e:
        logger.warning(f"Unpin all chat messages in {cid} - Sleep for {e.x} second(s)")
        raise e
    except (ChannelInvalid, ChannelPrivate, ChatAdminRequired, ChatNotModified, PeerIdInvalid):
        return False
    except Exception as e:
        logger.warning(f"Unpin chat messages in {cid} error: {e}", exc_info=True)

    return result
