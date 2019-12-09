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
import re
from copy import deepcopy

from pyrogram import Client, Filters, Message

from .. import glovar
from ..functions.channel import get_debug_text, send_debug, share_data
from ..functions.etc import bold, code, code_block, delay, get_command_context, get_command_type, get_now, lang
from ..functions.etc import mention_id, thread
from ..functions.file import save
from ..functions.filters import authorized_group, from_user, is_class_c, test_group
from ..functions.group import delete_message, get_config_text
from ..functions.telegram import get_group_info, send_message, send_report_message
from ..functions.tip import get_invite_link, get_keywords, tip_ot, tip_rm, tip_welcome

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["channel"], glovar.prefix)
                   & ~test_group & authorized_group
                   & from_user)
def channel(client: Client, message: Message) -> bool:
    # Channel config

    if not message or not message.chat:
        return True

    # Basic data
    gid = message.chat.id
    mid = message.message_id

    glovar.locks["message"].acquire()
    try:
        # Check permission
        if not is_class_c(None, message):
            return True

        aid = message.from_user.id
        r_message = message.reply_to_message

        # Bind a channel
        if r_message:
            # Text prefix
            text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                    f"{lang('action')}{lang('colon')}{code(lang('action_bind'))}\n")

            # Check the message
            if not r_message.forward_from_chat:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")
                thread(send_report_message, (15, client, gid, text))
                return True

            # Try to send a message to the channel
            cid = r_message.forward_from_chat.id
            glovar.configs[gid]["default"] = False
            glovar.configs[gid]["channel"] = cid
            save("configs")
            result = get_invite_link(client, "send", gid, True)

            # Check the result
            if not result:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")
                thread(send_report_message, (15, client, gid, text))
                return True
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
                         f"{lang('channel')}{lang('colon')}{code(cid)}\n")

            # Send the report message
            thread(send_report_message, (20, client, gid, text))

            # Send debug message
            send_debug(
                client=client,
                chat=message.chat,
                action=lang("config_change"),
                aid=aid,
                config_type=lang("action_bind"),
                more=str(cid)
            )

            return True

        # Change channel config
        command_type, command_context = get_command_context(message)

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_channel'))}\n")

        # Check command format
        if command_type not in {"text", "button"} or not command_context:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")
            thread(send_report_message, (15, client, gid, text))
            return True

        # Change the button config
        command_context = command_context.strip()
        glovar.configs[gid]["default"] = False
        glovar.configs[gid][f"channel_{command_type}"] = command_context
        save("configs")
        get_invite_link(client, "edit", gid, True)
        text += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
        send_debug(
            client=client,
            chat=message.chat,
            action=lang("config_change"),
            aid=aid,
            config_type="channel",
            more=command_type
        )

        # Send the report message
        thread(send_report_message, (20, client, gid, text))

        return True
    except Exception as e:
        logger.warning(f"Channel error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()
        delete_message(client, gid, mid)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["config"], glovar.prefix)
                   & ~test_group & authorized_group
                   & from_user)
def config(client: Client, message: Message) -> bool:
    # Request CONFIG session

    if not message or not message.chat:
        return True

    # Basic data
    gid = message.chat.id
    mid = message.message_id

    try:
        # Check permission
        if not is_class_c(None, message):
            return True

        # Check command format
        command_type = get_command_type(message)
        if not command_type or not re.search(f"^{glovar.sender}$", command_type, re.I):
            return True

        now = get_now()

        # Check the config lock
        if now - glovar.configs[gid]["lock"] < 310:
            return True

        # Set lock
        glovar.configs[gid]["lock"] = now
        save("configs")

        # Pre-process config
        default_config = deepcopy(glovar.default_config)
        type_list = set(default_config)
        type_list.discard("lock")
        for the_type in type_list:
            default_config[the_type] = bool(default_config[the_type])

        the_config = deepcopy(glovar.configs[gid])
        for the_type in type_list:
            the_config[the_type] = bool(the_config[the_type])

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
                "user_id": message.from_user.id,
                "config": the_config,
                "default": default_config
            }
        )

        # Send debug message
        text = get_debug_text(client, message.chat)
        text += (f"{lang('admin_group')}{lang('colon')}{code(message.from_user.id)}\n"
                 f"{lang('action')}{lang('colon')}{code(lang('config_create'))}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Config error: {e}", exc_info=True)
    finally:
        if is_class_c(None, message):
            delay(3, delete_message, [client, gid, mid])
        else:
            delete_message(client, gid, mid)

    return False


@Client.on_message(Filters.incoming & Filters.group
                   & Filters.command([f"config_{glovar.sender.lower()}"], glovar.prefix)
                   & ~test_group & authorized_group
                   & from_user)
def config_directly(client: Client, message: Message) -> bool:
    # Config the bot directly

    if not message or not message.chat:
        return True

    # Basic data
    gid = message.chat.id
    mid = message.message_id

    try:
        # Check permission
        if not is_class_c(None, message):
            return True

        aid = message.from_user.id
        success = True
        reason = lang("config_updated")
        new_config = deepcopy(glovar.configs[gid])
        text = f"{lang('admin_group')}{lang('colon')}{code(aid)}\n"

        # Check command format
        command_type, command_context = get_command_context(message)
        if command_type:
            if command_type == "show":
                text += f"{lang('action')}{lang('colon')}{code(lang('config_show'))}\n"
                text += get_config_text(new_config)
                thread(send_report_message, (30, client, gid, text))
                return True

            now = get_now()

            # Check the config lock
            if now - new_config["lock"] > 310:
                if command_type == "default":
                    new_config = deepcopy(glovar.default_config)
                else:
                    if command_context:
                        if command_type in {"captcha", "clean", "resend"}:
                            if command_context == "off":
                                new_config[command_type] = False
                            elif command_context == "on":
                                new_config[command_type] = True
                            else:
                                success = False
                                reason = lang("command_para")
                        elif command_type == "channel":
                            if command_context == "off":
                                new_config[command_type] = 0
                            else:
                                success = False
                                reason = lang("command_para")
                        elif command_type in {"keyword", "ot", "rm", "welcome"}:
                            if command_context == "off":
                                new_config[command_type] = ""
                            else:
                                success = False
                                reason = lang("command_para")
                        else:
                            success = False
                            reason = lang("command_type")
                    else:
                        success = False
                        reason = lang("command_lack")

                    if success:
                        new_config["default"] = False
            else:
                success = False
                reason = lang("config_locked")
        else:
            success = False
            reason = lang("command_usage")

        if success and new_config != glovar.configs[gid]:
            # Save new config
            glovar.configs[gid] = new_config
            save("configs")

            # Send debug message
            debug_text = get_debug_text(client, message.chat)
            debug_text += (f"{lang('admin_group')}{lang('colon')}{code(message.from_user.id)}\n"
                           f"{lang('action')}{lang('colon')}{code(lang('config_change'))}\n"
                           f"{lang('more')}{lang('colon')}{code(f'{command_type} {command_context}')}\n")
            thread(send_message, (client, glovar.debug_channel_id, debug_text))

        text += (f"{lang('action')}{lang('colon')}{code(lang('config_change'))}\n"
                 f"{lang('status')}{lang('colon')}{code(reason)}\n")
        thread(send_report_message, ((lambda x: 10 if x else 5)(success), client, gid, text))

        return True
    except Exception as e:
        logger.warning(f"Config directly error: {e}", exc_info=True)
    finally:
        delete_message(client, gid, mid)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["keyword"], glovar.prefix)
                   & ~test_group & authorized_group
                   & from_user)
def keyword(client: Client, message: Message) -> bool:
    # Keyword config

    if not message or not message.chat:
        return True

    # Basic data
    gid = message.chat.id
    mid = message.message_id

    glovar.locks["message"].acquire()
    try:
        # Check permission
        if not is_class_c(None, message):
            return True

        aid = message.from_user.id
        command_type, command_context = get_command_context(message)

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_keyword'))}\n")

        # Check command format
        if not command_type and not command_context:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")
            thread(send_report_message, (15, client, gid, text))
            return True

        # Config keyword text
        if command_type not in {"button", "link"}:
            command_type = get_command_type(message)
            result = get_keywords(command_type)

            # Check the result
            if not result:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")
                thread(send_report_message, (15, client, gid, text))
                return True
            else:
                glovar.configs[gid]["default"] = False
                glovar.configs[gid]["keyword"] = command_type
                save("configs")
                text += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"

            # Send the report message
            thread(send_report_message, (20, client, gid, text))

            # Send debug message
            send_debug(
                client=client,
                chat=message.chat,
                action=lang("config_change"),
                aid=aid,
                config_type="keyword",
                more="text"
            )

            return True

        # Config keyword message button
        command_context = command_context.strip()
        glovar.configs[gid]["default"] = False
        glovar.configs[gid][f"keyword_{command_type}"] = command_context
        save("configs")
        text += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
        send_debug(
            client=client,
            chat=message.chat,
            action=lang("config_change"),
            aid=aid,
            config_type="keyword",
            more=command_type
        )

        # Send the report message
        thread(send_report_message, (20, client, gid, text))

        return True
    except Exception as e:
        logger.warning(f"Keyword error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()
        delete_message(client, gid, mid)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["ot"], glovar.prefix)
                   & ~test_group & authorized_group
                   & from_user)
def ot(client: Client, message: Message) -> bool:
    # OT config

    if not message or not message.chat:
        return True

    # Basic data
    gid = message.chat.id
    mid = message.message_id

    glovar.locks["message"].acquire()
    try:
        # Check permission
        if not is_class_c(None, message):
            return True

        aid = message.from_user.id
        r_message = message.reply_to_message
        command_type, command_context = get_command_context(message)

        # Send OT tip
        if r_message:
            return tip_ot(client, gid, r_message.message_id)
        elif not command_type:
            return tip_ot(client, gid)

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_ot'))}\n")

        # Check command format
        if not command_type and not command_context:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")
            thread(send_report_message, (15, client, gid, text))
            return True

        # Config OT text
        if command_type not in {"button", "link"}:
            command_type = get_command_type(message)
            glovar.configs[gid]["default"] = False
            glovar.configs[gid]["ot"] = command_type
            save("configs")
            text += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"

            # Send the report message
            thread(send_report_message, (20, client, gid, text))

            # Send debug message
            send_debug(
                client=client,
                chat=message.chat,
                action=lang("config_change"),
                aid=aid,
                config_type="ot",
                more="text"
            )

            return True

        # Config OT message button
        command_context = command_context.strip()
        glovar.configs[gid]["default"] = False
        glovar.configs[gid][f"ot_{command_type}"] = command_context
        save("configs")
        text += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
        send_debug(
            client=client,
            chat=message.chat,
            action=lang("config_change"),
            aid=aid,
            config_type="ot",
            more=command_type
        )

        # Send the report message
        thread(send_report_message, (20, client, gid, text))

        return True
    except Exception as e:
        logger.warning(f"Ot error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()
        delete_message(client, gid, mid)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["resend"], glovar.prefix)
                   & ~test_group & authorized_group
                   & from_user)
def resend(client: Client, message: Message) -> bool:
    # Resend the group link message

    if not message or not message.chat:
        return True

    # Basic data
    gid = message.chat.id
    mid = message.message_id

    glovar.locks["message"].acquire()
    try:
        # Check permission
        if not is_class_c(None, message):
            return True

        aid = message.from_user.id

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_resend'))}\n")

        # Try to send
        result = get_invite_link(client, "send", gid, True)

        # Check the result
        if not result:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")
            thread(send_report_message, (15, client, gid, text))
            return True

        # Send debug message
        send_debug(
            client=client,
            chat=message.chat,
            action=lang("action_resend"),
            aid=aid
        )

        # Send the report message
        text += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
        thread(send_report_message, (20, client, gid, text))

        return True
    except Exception as e:
        logger.warning(f"Resend begin error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()
        delete_message(client, gid, mid)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["rm"], glovar.prefix)
                   & ~test_group & authorized_group
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
        if not is_class_c(None, message):
            return True

        aid = message.from_user.id
        r_message = message.reply_to_message
        command_type, command_context = get_command_context(message)

        # Send RM tip
        if r_message:
            text = glovar.configs[gid]["rm"]
            if text:
                return tip_rm(client, gid, text, r_message.message_id)
            else:
                return True

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_rm'))}\n")

        # Check command format
        if not command_type and not command_context:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")
            thread(send_report_message, (15, client, gid, text))
            return True

        # Config RM text
        if command_type not in {"button", "link"}:
            command_type = get_command_type(message)
            glovar.configs[gid]["default"] = False
            glovar.configs[gid]["rm"] = command_type
            save("configs")
            text += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"

            # Send the report message
            thread(send_report_message, (20, client, gid, text))

            # Send debug message
            send_debug(
                client=client,
                chat=message.chat,
                action=lang("config_change"),
                aid=aid,
                config_type="rm",
                more="text"
            )

            return True

        # Config RM message button
        command_context = command_context.strip()
        glovar.configs[gid]["default"] = False
        glovar.configs[gid][f"rm_{command_type}"] = command_context
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


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["show"], glovar.prefix)
                   & ~test_group & authorized_group
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
        if not is_class_c(None, message):
            return True

        aid = message.from_user.id
        command_type = get_command_type(message)

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_show'))}\n")

        # Check command format
        type_list = set(glovar.default_config)
        for the_type in ["default", "lock", "clean", "resend", "channel"]:
            type_list.discard(the_type)

        if not command_type or command_type not in type_list:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")
            thread(send_report_message, (15, client, gid, text))
            return True

        # Get the config
        result = glovar.configs[gid][command_type] or lang("reason_none")
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


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["welcome"], glovar.prefix)
                   & ~test_group & authorized_group
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
        if not is_class_c(None, message):
            return True

        aid = message.from_user.id
        r_message = message.reply_to_message
        command_type, command_context = get_command_context(message)

        # Send welcome tip
        if r_message:
            text = glovar.configs[gid]["welcome"]
            text and tip_welcome(client, r_message)
            return True

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{code(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_welcome'))}\n")

        # Check command format
        if not command_type and not command_context:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")
            thread(send_report_message, (15, client, gid, text))
            return True

        # Config welcome text
        if command_type not in {"button", "link"}:
            command_type = get_command_type(message)
            glovar.configs[gid]["default"] = False
            glovar.configs[gid]["welcome"] = command_type
            save("configs")
            text += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"

            # Send the report message
            thread(send_report_message, (20, client, gid, text))

            # Send debug message
            send_debug(
                client=client,
                chat=message.chat,
                action=lang("config_change"),
                aid=aid,
                config_type="welcome",
                more="text"
            )

            return True

        # Config welcome message button
        command_context = command_context.strip()
        glovar.configs[gid]["default"] = False
        glovar.configs[gid][f"welcome_{command_type}"] = command_context
        save("configs")
        text += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
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


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["version"], glovar.prefix)
                   & test_group
                   & from_user)
def version(client: Client, message: Message) -> bool:
    # Check the program's version
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n\n"
                f"{lang('version')}{lang('colon')}{bold(glovar.version)}\n")
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)

    return False
