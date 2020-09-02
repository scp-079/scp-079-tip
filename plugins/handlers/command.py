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
import re
from copy import deepcopy
from subprocess import run, PIPE

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from .. import glovar
from ..functions.channel import get_debug_text, send_debug, share_data
from ..functions.command import (command_error, delete_normal_command, delete_shared_command, get_command_context,
                                 get_command_type)
from ..functions.config import conflict_config, get_config_text, kws_config_occupy, update_config
from ..functions.etc import (code, code_block, general_link, get_int, get_now, get_readable_time, lang,
                             mention_id, thread)
from ..functions.file import save
from ..functions.filters import authorized_group, from_user, is_class_c, is_from_user, test_group
from ..functions.group import delete_message
from ..functions.markup import get_text_and_markup_tip
from ..functions.program import restart_program, update_program
from ..functions.telegram import (forward_messages, get_group_info, get_start, pin_chat_message, send_message,
                                  send_report_message)
from ..functions.tip import get_invite_link, tip_ot, tip_rm, tip_welcome
from ..functions.user import add_start

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(filters.incoming & filters.group & filters.reply & filters.command(["channel"], glovar.prefix)
                   & authorized_group
                   & from_user)
def channel_bind(client: Client, message: Message) -> bool:
    # Bind a channel
    result = False

    glovar.locks["config"].acquire()

    try:
        # Basic data
        gid = message.chat.id
        aid = message.from_user.id
        r_message = message.reply_to_message

        # Check permission
        if not is_class_c(None, None, message):
            return False

        # Check the replied message
        if not r_message or not is_from_user(None, None, r_message):
            return False

        # Check the message
        if not r_message.forward_from_chat:
            return command_error(client, message, lang("action_bind"), lang("command_usage"),
                                 lang("error_channel_bind_reply"))

        # Try to send a message to the channel
        cid = r_message.forward_from_chat.id

        glovar.channels[gid]["aid"] = aid
        glovar.channels[gid]["cid"] = cid
        save("channels")

        glovar.configs[gid]["default"] = False
        glovar.configs[gid]["channel"] = True
        save("configs")

        result = get_invite_link(
            client=client,
            the_type="send",
            gid=gid,
            manual=True
        )

        # Check the result
        if not result:
            return command_error(client, message, lang("action_bind"), lang("command_usage"),
                                 lang("error_channel_bind_send"))

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_bind'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
                f"{lang('channel')}{lang('colon')}{code(cid)}\n")

        # Send the report message
        send_report_message(20, client, gid, text)

        # Send debug message
        send_debug(
            client=client,
            chat=message.chat,
            action=lang("config_change"),
            aid=aid,
            config_type=lang("action_bind"),
            more=str(cid)
        )

        result = True
    except Exception as e:
        logger.warning(f"Channel bind error: {e}", exc_info=True)
    finally:
        glovar.locks["config"].release()
        delete_normal_command(client, message)

    return result


@Client.on_message(filters.incoming & filters.group & filters.reply & filters.command(["channel"], glovar.prefix)
                   & authorized_group
                   & from_user)
def channel_config(client: Client, message: Message) -> bool:
    # Config the channel text or button
    result = False

    glovar.locks["config"].acquire()

    try:
        # Basic data
        gid = message.chat.id
        aid = message.from_user.id

        # Check permission
        if not is_class_c(None, None, message):
            return False

        # Change channel config
        command_type, command_context = get_command_context(message)

        # Check command format
        if command_type not in {"text", "button"} or not command_context:
            return command_error(client, message, lang("action_channel"), lang("command_usage"))

        # Change the button config
        glovar.channels[gid]["aid"] = aid
        glovar.channels[gid][command_type] = command_context
        save("channels")
        get_invite_link(
            client=client,
            the_type="edit",
            gid=gid,
            manual=True
        )

        # Send the report message
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_channel'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n")
        send_report_message(20, client, gid, text)

        # Send debug
        send_debug(
            client=client,
            chat=message.chat,
            action=lang("config_change"),
            aid=aid,
            config_type="channel",
            more=command_type
        )

        result = True
    except Exception as e:
        logger.warning(f"Channel config error: {e}", exc_info=True)
    finally:
        glovar.locks["config"].release()
        delete_normal_command(client, message)

    return result


@Client.on_message(filters.incoming & filters.group & filters.command(["close", "open", "resend"], glovar.prefix)
                   & authorized_group
                   & from_user)
def channel_trigger(client: Client, message: Message) -> bool:
    # Channel trigger
    result = False

    glovar.locks["config"].acquire()

    try:
        # Basic data
        gid = message.chat.id
        aid = message.from_user.id

        # Check permission
        if not is_class_c(None, None, message):
            return True

        # Get command
        command = message.command[0]

        # Get command type
        command_type = get_command_type(message)

        # Try to send
        if command == "close":
            result = get_invite_link(
                client=client,
                the_type="close",
                gid=gid,
                manual=True,
                reason=command_type
            )
        elif command == "open":
            result = get_invite_link(
                client=client,
                the_type="open",
                gid=gid,
                manual=True
            )
        elif command == "resend":
            result = get_invite_link(
                client=client,
                the_type="send",
                gid=gid,
                manual=True
            )
        else:
            result = None

        # Check the result
        if not result:
            return command_error(client, message, lang(f"action_{command}"), lang("command_usage"))

        # Send the report message
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang(f'action_{command}'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n")
        send_report_message(20, client, gid, text)

        # Send debug message
        send_debug(
            client=client,
            chat=message.chat,
            action=lang(f"action_{command}"),
            aid=aid
        )

        result = True
    except Exception as e:
        logger.warning(f"Channel trigger error: {e}", exc_info=True)
    finally:
        glovar.locks["config"].release()
        delete_normal_command(client, message)

    return result


@Client.on_message(filters.incoming & filters.group & filters.command(["config"], glovar.prefix)
                   & authorized_group
                   & from_user)
def config(client: Client, message: Message) -> bool:
    # Request CONFIG session
    result = False

    glovar.locks["config"].acquire()

    try:
        # Basic data
        gid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id

        # Check permission
        if not is_class_c(None, None, message):
            return False

        # Check command format
        command_type, command_context = get_command_context(message)

        if not command_type or not re.search(f"^{glovar.sender}$", command_type, re.I):
            return False

        now = get_now()

        # Check the config lock
        if now - glovar.configs[gid]["lock"] < 310:
            return command_error(client, message, lang("config_change"), lang("command_flood"))

        # Private check
        if command_context == "private":
            result = forward_messages(
                client=client,
                cid=glovar.compromise_channel_id,
                fid=gid,
                mids=mid
            )

            if not result:
                return False

            text = (f"{lang('project')}{lang('colon')}{code(glovar.sender)}\n"
                    f"{lang('user_id')}{lang('colon')}{code(aid)}\n"
                    f"{lang('level')}{lang('colon')}{code(lang('config_create'))}\n"
                    f"{lang('rule')}{lang('colon')}{code(lang('rule_custom'))}\n")
            result = send_message(client, glovar.compromise_channel_id, text, result.message_id)
        else:
            result = None

        # Set lock
        glovar.configs[gid]["lock"] = now
        save("configs")

        # Ask CONFIG generate a config session
        group_name, group_link = get_group_info(client, message.chat)
        share_data(
            client=client,
            receivers=["CONFIG"],
            action="config",
            action_type="ask",
            data={
                "project_name": glovar.project_name,
                "project_link": glovar.project_link,
                "group_id": gid,
                "group_name": group_name,
                "group_link": group_link,
                "user_id": aid,
                "private": command_context == "private",
                "config": glovar.configs[gid],
                "default": glovar.default_config
            }
        )

        # Send debug message
        text = get_debug_text(client, message.chat)
        text += (f"{lang('admin_group')}{lang('colon')}{code(message.from_user.id)}\n"
                 f"{lang('action')}{lang('colon')}{code(lang('config_create'))}\n")

        if result:
            text += f"{lang('evidence')}{lang('colon')}{general_link(result.message_id, result.link)}\n"

        thread(send_message, (client, glovar.debug_channel_id, text))

        result = True
    except Exception as e:
        logger.warning(f"Config error: {e}", exc_info=True)
    finally:
        glovar.locks["config"].release()
        delete_shared_command(client, message)

    return result


@Client.on_message(filters.incoming & filters.group
                   & filters.command([f"config_{glovar.sender.lower()}"], glovar.prefix)
                   & authorized_group
                   & from_user)
def config_directly(client: Client, message: Message) -> bool:
    # Config the bot directly
    result = False

    glovar.locks["config"].acquire()

    try:
        # Basic data
        gid = message.chat.id
        aid = message.from_user.id
        now = get_now()

        # Check permission
        if not is_class_c(None, None, message):
            return False

        # Get get the command
        command_type, command_context = get_command_context(message)

        # Check the command
        if not command_type:
            return command_error(client, message, lang("config_change"), lang("command_lack"))

        # Get the config
        new_config = deepcopy(glovar.configs[gid])

        # Show the config
        if command_type == "show":
            text = (f"{lang('admin_group')}{lang('colon')}{code(aid)}\n"
                    f"{lang('action')}{lang('colon')}{code(lang('config_show'))}\n"
                    f"{get_config_text(new_config)}\n")
            return send_report_message(30, client, gid, text)

        # Check the config lock
        if now - new_config["lock"] < 310:
            return command_error(client, message, lang("config_change"), lang("config_locked"))

        # Set the config to default status
        if command_type == "default":
            new_config = deepcopy(glovar.default_config)
            new_config["lock"] = now
            return update_config(client, message, new_config, "default")

        # Check the command format
        if not command_context:
            return command_error(client, message, lang("config_change"), lang("command_lack"))

        # Check the command type
        if command_type not in {"captcha", "alone", "clean", "resend", "channel", "cancel", "hold", "keyword",
                                "white", "ot", "rm", "welcome"}:
            return command_error(client, message, lang("config_change"), lang("command_type"))

        # New settings
        if command_context == "off":
            new_config[command_type] = False
        elif command_context == "on":
            new_config[command_type] = True
        else:
            return command_error(client, message, lang("config_change"), lang("command_para"))

        new_config = conflict_config(new_config, ["cancel", "hold"], command_type)
        new_config["default"] = False
        result = update_config(client, message, new_config, f"{command_type} {command_context}")
    except Exception as e:
        logger.warning(f"Config directly error: {e}", exc_info=True)
    finally:
        glovar.locks["config"].release()
        delete_normal_command(client, message)

    return result


@Client.on_message(filters.incoming & filters.group & filters.command(["hold"], glovar.prefix)
                   & authorized_group
                   & from_user)
def hold(client: Client, message: Message) -> bool:
    # Hold the pinned message
    result = False

    glovar.locks["config"].acquire()

    try:
        # Basic data
        gid = message.chat.id
        aid = message.from_user.id
        r_message = message.reply_to_message

        # Check permission
        if not is_class_c(None, None, message):
            return False

        # Check the message
        if not r_message:
            return command_error(client, message, lang("action_hold"), lang("command_usage"))

        # Hold the message
        glovar.pinned_ids[gid] = r_message.message_id
        save("pinned_ids")
        thread(pin_chat_message, (client, gid, r_message.message_id))

        # Generate the text
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_hold'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
                f"{lang('pinned_message')}{lang('colon')}{code(r_message.message_id)}\n")

        # Send the report message
        send_report_message(20, client, gid, text)

        # Send debug message
        send_debug(
            client=client,
            chat=message.chat,
            action=lang("config_change"),
            aid=aid,
            config_type=lang("action_hold"),
            more=str(r_message.message_id)
        )

        result = True
    except Exception as e:
        logger.warning(f"Hold error: {e}", exc_info=True)
    finally:
        glovar.locks["config"].release()
        delete_normal_command(client, message)

    return result


@Client.on_message(filters.incoming & filters.group & filters.command(["keyword", "keywords", "kws"], glovar.prefix)
                   & authorized_group
                   & from_user)
def kws(client: Client, message: Message) -> bool:
    # Request a custom keywords setting session
    result = False

    glovar.locks["config"].acquire()

    try:
        # Basic data
        gid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        now = message.date or get_now()

        # Check permission
        if not is_class_c(None, None, message):
            return False

        # Check the group status
        if now < glovar.keywords[gid]["lock"] + 600:
            aid = glovar.keywords[gid]["aid"]
            return command_error(client, message, lang("action_kws_start"), lang("error_kws_occupied"),
                                 lang("detail_kws_occupied").format(aid))

        # Save evidence
        result = forward_messages(
            client=client,
            cid=glovar.compromise_channel_id,
            fid=gid,
            mids=mid
        )

        if not result:
            return False

        text = (f"{lang('project')}{lang('colon')}{code(glovar.sender)}\n"
                f"{lang('user_id')}{lang('colon')}{code(aid)}\n"
                f"{lang('level')}{lang('colon')}{code(lang('config_create'))}\n"
                f"{lang('rule')}{lang('colon')}{code(lang('rule_custom'))}\n")
        result = send_message(client, glovar.compromise_channel_id, text, result.message_id)

        # Save the data
        glovar.keywords[gid]["lock"] = now
        glovar.keywords[gid]["aid"] = aid
        kws_config_occupy(gid, aid)
        save("keywords")

        # Add start status
        key = add_start(get_now() + 180, gid, aid, "kws")

        # Send the report message
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_kws_start'))}\n"
                f"{lang('description')}{lang('colon')}{code(lang('config_button'))}\n")
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=lang("config_go"),
                        url=get_start(client, key)
                    )
                ]
            ]
        )
        send_report_message(180, client, gid, text, None, markup)

        # Send debug message
        text = get_debug_text(client, message.chat)
        text += (f"{lang('admin_group')}{lang('colon')}{code(message.from_user.id)}\n"
                 f"{lang('action')}{lang('colon')}{code(lang('config_create'))}\n"
                 f"{lang('evidence')}{lang('colon')}{general_link(result.message_id, result.link)}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))

        result = True
    except Exception as e:
        logger.warning(f"Kws error: {e}", exc_info=True)
    finally:
        glovar.locks["config"].release()
        delete_normal_command(client, message)

    return result


@Client.on_message(filters.incoming & filters.group & filters.command(["ot"], glovar.prefix)
                   & authorized_group
                   & from_user)
def ot(client: Client, message: Message) -> bool:
    # OT config
    result = False

    glovar.locks["message"].acquire()

    try:
        # Basic data
        gid = message.chat.id
        aid = message.from_user.id
        r_message = message.reply_to_message

        # Check permission
        if not is_class_c(None, None, message):
            return True

        # Get command type
        command_type = get_command_type(message)

        # Send OT tip
        if r_message:
            return tip_ot(client, gid, r_message.message_id)
        elif not command_type:
            return tip_ot(client, gid)

        # Check the reply length
        if len(command_type) > 1500:
            return command_error(client, message, lang("action_ot"), lang("command_para"),
                                 lang("error_exceed_reply"))

        # Check the reply config
        _, markup = get_text_and_markup_tip(gid, command_type)

        if markup is False:
            return command_error(client, message, lang("action_ot"), lang("command_para"),
                                 lang("error_markup_invalid"))

        # Config OT
        last_editor = glovar.ots[gid]["aid"]
        glovar.ots[gid]["aid"] = aid
        glovar.ots[gid]["old"] = deepcopy(glovar.ots[gid].get("reply", ""))
        glovar.ots[gid]["reply"] = command_type
        save("ots")

        # Send the report message
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_ot'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
                f"{lang('last_editor')}{lang('colon')}{code(last_editor)}\n"
                f"{lang('old_reply')}{lang('colon')}" + code("-" * 16) + "\n\n")
        text += code_block(glovar.ots[gid]["old"])
        send_report_message(20, client, gid, text)

        # Send debug message
        send_debug(
            client=client,
            chat=message.chat,
            action=lang("config_change"),
            aid=aid,
            config_type="ot",
            more=command_type
        )

        result = True
    except Exception as e:
        logger.warning(f"Ot error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()
        delete_normal_command(client, message)

    return result


@Client.on_message(filters.incoming & filters.group & filters.command(["restart"], glovar.prefix)
                   & test_group
                   & from_user)
def restart(client: Client, message: Message) -> bool:
    # Restart the program
    result = False

    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id

        # Get command type
        command_type = get_command_type(message)

        # Check the command type
        if command_type and command_type.upper() != glovar.sender:
            return False

        # Generate the text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n\n"
                f"{lang('project')}{lang('colon')}{code(glovar.sender)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('program_restart'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('command_received'))}\n")

        # Send the report message
        send_message(client, cid, text, mid)

        # Restart the program
        result = restart_program()
    except Exception as e:
        logger.warning(f"Restart error: {e}", exc_info=True)

    return result


@Client.on_message(filters.incoming & filters.group & filters.command(["rm"], glovar.prefix)
                   & authorized_group
                   & from_user)
def rm(client: Client, message: Message) -> bool:
    # RM config

    if not message or not message.chat:
        return True

    # Basic data
    gid = message.chat.id
    mid = message.message_id

    glovar.locks["message"].acquire()
    try:
        # Check permission
        if not is_class_c(None, None, message):
            return True

        aid = message.from_user.id
        r_message = message.reply_to_message
        command_type, command_context = get_command_context(message)

        # Send RM tip
        text = glovar.configs[gid].get("rm_text")

        if r_message:
            return tip_rm(client, gid, text, r_message.message_id)
        elif not command_type:
            return tip_rm(client, gid, text)

        # Show the config
        if command_type in {"text", "button", "link"} and not command_context:
            # Text prefix
            text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                    f"{lang('action')}{lang('colon')}{code(lang('action_show'))}\n")

            # Get the config
            result = glovar.configs[gid].get(f"rm_{command_type}") or lang("reason_none")
            text += (f"{lang('result')}{lang('colon')}" + "-" * 24 + "\n\n"
                     f"{code_block(result)}\n")

            # Check the text
            if len(text) > 4000:
                text = code_block(result)

            # Send the report message
            return thread(send_report_message, (20, client, gid, text))

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_rm'))}\n")

        # Check command format
        if not command_type or command_type not in {"text", "button", "link"} or not command_context:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")
            thread(send_report_message, (15, client, gid, text))
            return True

        # Config RM
        glovar.configs[gid]["default"] = False
        glovar.configs[gid][f"rm_{command_type}"] = command_context.strip()
        save("configs")
        text += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
        send_debug(
            client=client,
            chat=message.chat,
            action=lang("config_change"),
            aid=aid,
            config_type="rm",
            more=command_type
        )

        # Send the report message
        thread(send_report_message, (20, client, gid, text))

        return True
    except Exception as e:
        logger.warning(f"Rm begin error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()
        delete_message(client, gid, mid)

    return False


@Client.on_message(filters.incoming & filters.group & filters.command(["show"], glovar.prefix)
                   & authorized_group
                   & from_user)
def show(client: Client, message: Message) -> bool:
    # Show the config text

    if not message or not message.chat:
        return True

    # Basic data
    gid = message.chat.id
    mid = message.message_id

    glovar.locks["message"].acquire()
    try:
        # Check permission
        if not is_class_c(None, None, message):
            return True

        aid = message.from_user.id
        command_type = get_command_type(message)

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_show'))}\n")

        # Check command format
        type_list = set(glovar.default_config)

        for the_type in ["default", "lock", "captcha", "alone", "clean", "resend", "channel", "hold"]:
            type_list.discard(the_type)

        if not command_type or command_type not in type_list:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")
            thread(send_report_message, (15, client, gid, text))
            return True

        # Get the config
        result = glovar.configs[gid].get(command_type) or lang("reason_none")
        text += (f"{lang('result')}{lang('colon')}" + "-" * 24 + "\n\n"
                 f"{code_block(result)}\n")

        # Check the text
        if len(text) > 4000:
            text = code_block(result)

        # Send the report message
        thread(send_report_message, (20, client, gid, text))

        return True
    except Exception as e:
        logger.warning(f"Show error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()
        delete_message(client, gid, mid)

    return False


@Client.on_message(filters.incoming & filters.group & filters.command(["welcome"], glovar.prefix)
                   & authorized_group
                   & from_user)
def welcome(client: Client, message: Message) -> bool:
    # Welcome config

    if not message or not message.chat:
        return True

    # Basic data
    gid = message.chat.id
    mid = message.message_id

    glovar.locks["message"].acquire()
    try:
        # Check permission
        if not is_class_c(None, None, message):
            return True

        aid = message.from_user.id
        r_message = message.reply_to_message
        command_type, command_context = get_command_context(message)

        # Send welcome tip
        if r_message:
            return tip_welcome(client, r_message, None, 0, None, True)

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_welcome'))}\n")

        # Show the config
        if not command_type or (command_type and command_type in {"text", "button", "link"} and not command_context):
            # Check command
            if not command_type:
                command_type = "text"

            # Text prefix
            text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                    f"{lang('action')}{lang('colon')}{code(lang('action_show'))}\n")

            # Get the config
            result = glovar.configs[gid].get(f"welcome_{command_type}") or lang("reason_none")
            text += (f"{lang('result')}{lang('colon')}" + "-" * 24 + "\n\n"
                     f"{code_block(result)}\n")

            # Check the text
            if len(text) > 4000:
                text = code_block(result)

            # Send the report message
            return thread(send_report_message, (20, client, gid, text))

        # Check command format
        if not command_type or command_type not in {"text", "button", "link"} or not command_context:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")
            thread(send_report_message, (15, client, gid, text))
            return True

        # Config welcome
        command_context = command_context.strip()
        glovar.configs[gid]["default"] = False
        glovar.configs[gid][f"welcome_{command_type}"] = command_context
        save("configs")
        text += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"

        if (command_type == "text"
                and ("$mention_name" not in command_context and "$mention_id" not in command_context)
                and glovar.captcha_id in glovar.admin_ids[gid]
                and glovar.configs[gid].get("captcha")):
            text += f"{lang('tip')}{lang('colon')}{code(lang('tip_captcha'))}\n"

        send_debug(
            client=client,
            chat=message.chat,
            action=lang("config_change"),
            aid=aid,
            config_type="welcome",
            more=command_type
        )

        # Send the report message
        thread(send_report_message, (20, client, gid, text))

        return True
    except Exception as e:
        logger.warning(f"Welcome error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()
        delete_message(client, gid, mid)

    return False


@Client.on_message(filters.incoming & filters.group & filters.command(["update"], glovar.prefix)
                   & test_group
                   & from_user)
def update(client: Client, message: Message) -> bool:
    # Update the program
    result = False

    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id

        # Get command type
        command_type = get_command_type(message)

        # Check the command type
        if command_type and command_type.upper() != glovar.sender:
            return False

        # Generate the text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n\n"
                f"{lang('project')}{lang('colon')}{code(glovar.sender)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('program_update'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('command_received'))}\n")

        # Send the report message
        send_message(client, cid, text, mid)

        # Update the program
        glovar.updating = True
        result = update_program()
    except Exception as e:
        logger.warning(f"Update error: {e}", exc_info=True)

    return result


@Client.on_message(filters.incoming & filters.group & filters.command(["version"], glovar.prefix)
                   & test_group
                   & from_user)
def version(client: Client, message: Message) -> bool:
    # Check the program's version
    result = False

    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id

        # Get command type
        command_type = get_command_type(message)

        # Check the command type
        if command_type and command_type.upper() != glovar.sender:
            return False

        # Check update status
        if glovar.updating:
            text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n\n"
                    f"{lang('project')}{lang('colon')}{code(glovar.sender)}\n"
                    f"{lang('status')}{lang('colon')}{code(lang('program_updating'))}\n")
            return thread(send_message, (client, cid, text, mid))

        # Version info
        git_change = bool(run("git diff-index HEAD --", stdout=PIPE, shell=True).stdout.decode().strip())
        git_date = run("git log -1 --format='%at'", stdout=PIPE, shell=True).stdout.decode()
        git_date = get_readable_time(get_int(git_date), "%Y/%m/%d %H:%M:%S")
        git_hash = run("git rev-parse --short HEAD", stdout=PIPE, shell=True).stdout.decode()
        get_hash_link = f"https://github.com/scp-079/scp-079-{glovar.sender.lower()}/commit/{git_hash}"
        command_date = get_readable_time(message.date, "%Y/%m/%d %H:%M:%S")

        # Generate the text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n\n"
                f"{lang('project')}{lang('colon')}{code(glovar.sender)}\n"
                f"{lang('version')}{lang('colon')}{code(glovar.version)}\n"
                f"{lang('git_change')}{lang('colon')}{code(git_change)}\n"
                f"{lang('git_hash')}{lang('colon')}{general_link(git_hash, get_hash_link)}\n"
                f"{lang('git_date')}{lang('colon')}{code(git_date)}\n"
                f"{lang('command_date')}{lang('colon')}{code(command_date)}\n")

        # Send the report message
        result = bool(send_message(client, cid, text, mid))
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)

    return result
