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

from pyrogram import Client, Filters, Message

from .. import glovar
from ..functions.channel import get_debug_text
from ..functions.etc import code, general_link, get_filename, get_forward_name, get_full_name, get_now, get_text
from ..functions.etc import lang, mention_id, thread
from ..functions.file import save
from ..functions.filters import authorized_group, class_d, declared_message, exchange_channel, from_user, hide_channel
from ..functions.filters import is_ban_text, is_bio_text, is_class_d_user, is_declared_message, is_high_score_user
from ..functions.filters import is_keyword_text, is_nm_text, is_regex_text, is_rm_text, is_watch_user, is_wb_text
from ..functions.filters import new_group, test_group
from ..functions.group import leave_group
from ..functions.ids import init_group_id, init_user_id
from ..functions.receive import receive_add_bad, receive_config_commit, receive_clear_data
from ..functions.receive import receive_config_reply, receive_config_show, receive_declared_message
from ..functions.receive import receive_help_welcome, receive_leave_approve, receive_regex, receive_refresh
from ..functions.receive import receive_remove_bad, receive_remove_score, receive_remove_watch, receive_rollback
from ..functions.receive import receive_text_data, receive_user_score, receive_watch_user
from ..functions.telegram import get_admins, get_user_bio, send_message
from ..functions.timers import backup_files, send_count
from ..functions.tip import tip_keyword, tip_rm, tip_welcome

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & ~Filters.service
                   & ~test_group & authorized_group
                   & from_user & ~class_d
                   & ~declared_message)
def check(client: Client, message: Message) -> bool:
    # Check the messages sent from groups
    glovar.locks["message"].acquire()
    try:
        # Basic data
        gid = message.chat.id
        mid = message.message_id
        now = message.date or get_now()

        # Check the config
        if not glovar.configs[gid]["keyword"] and not glovar.configs[gid]["rm"]:
            return True

        # Check the forward from name
        forward_name = get_forward_name(message, True, True)

        if forward_name and is_nm_text(forward_name):
            return True

        # Check the user's name
        name = get_full_name(message.from_user, True, True)

        if name and is_nm_text(name):
            return True

        # Check the text
        message_text = get_text(message, True, True)

        if is_ban_text(message_text, False):
            return True

        if is_regex_text("del", message_text):
            return True

        # File name
        filename = get_filename(message, True, True)

        if is_ban_text(filename, False):
            return True

        if is_regex_text("fil", filename):
            return True

        if is_regex_text("del", filename):
            return True

        # User status
        if is_watch_user(message.from_user, "ban", now):
            return True

        if is_watch_user(message.from_user, "delete", now):
            return True

        if is_high_score_user(message.from_user):
            return True

        # Check declare status
        if is_declared_message(None, message):
            return True

        # Check keyword
        detection = is_keyword_text(message)

        if detection:
            return tip_keyword(client, message, detection)

        # Check rm
        detection = is_rm_text(message)

        if detection:
            return tip_rm(client, gid, detection, mid)

        return True
    except Exception as e:
        logger.warning(f"Check error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.new_chat_members
                   & ~test_group & ~new_group & authorized_group
                   & from_user & ~class_d
                   & ~declared_message)
def check_join(client: Client, message: Message) -> bool:
    # Check new joined user
    glovar.locks["message"].acquire()
    try:
        # Basic data
        gid = message.chat.id

        # Word with CAPTCHA
        if glovar.configs[gid].get("captcha") and glovar.captcha_id in glovar.admin_ids[gid]:
            return True

        for new in message.new_chat_members:
            # Basic data
            uid = new.id

            # Check if the user is Class D personnel
            if is_class_d_user(new):
                return True

            # Check name
            name = get_full_name(new, True, True)

            if name and (is_nm_text(name) or is_wb_text(name, False)):
                return True

            # Check bio
            bio = get_user_bio(client, uid, True, True)

            if bio and (is_bio_text(bio) or is_wb_text(bio, False)):
                return True

            # Check declare status
            if is_declared_message(None, message):
                return True

            # Init the user's status
            if not init_user_id(uid):
                continue

        # Welcome
        tip_welcome(client, message)

        return True
    except Exception as e:
        logger.warning(f"Check join error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return False


@Client.on_message(Filters.incoming & Filters.channel & ~Filters.command(glovar.all_commands, glovar.prefix)
                   & hide_channel, group=-1)
def exchange_emergency(client: Client, message: Message) -> bool:
    # Sent emergency channel transfer request
    try:
        # Read basic information
        data = receive_text_data(message)

        if not data:
            return True

        sender = data["from"]
        receivers = data["to"]
        action = data["action"]
        action_type = data["type"]
        data = data["data"]

        if "EMERGENCY" not in receivers:
            return True

        if action != "backup":
            return True

        if action_type != "hide":
            return True

        if data is True:
            glovar.should_hide = data
        elif data is False and sender == "MANAGE":
            glovar.should_hide = data

        project_text = general_link(glovar.project_name, glovar.project_link)
        hide_text = (lambda x: lang("enabled") if x else "disabled")(glovar.should_hide)
        text = (f"{lang('project')}{lang('colon')}{project_text}\n"
                f"{lang('action')}{lang('colon')}{code(lang('transfer_channel'))}\n"
                f"{lang('emergency_channel')}{lang('colon')}{code(hide_text)}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Exchange emergency error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group
                   & (Filters.new_chat_members | Filters.group_chat_created | Filters.supergroup_chat_created)
                   & ~test_group & new_group
                   & from_user)
def init_group(client: Client, message: Message) -> bool:
    # Initiate new groups
    try:
        # Basic data
        gid = message.chat.id
        inviter = message.from_user

        # Text prefix
        text = get_debug_text(client, message.chat)

        # Check permission
        if inviter.id == glovar.user_id:
            # Remove the left status
            if gid in glovar.left_group_ids:
                glovar.left_group_ids.discard(gid)
                save("left_group_ids")

            # Update group's admin list
            if not init_group_id(gid):
                return True

            admin_members = get_admins(client, gid)

            if admin_members:
                glovar.admin_ids[gid] = {admin.user.id for admin in admin_members
                                         if ((not admin.user.is_bot and not admin.user.is_deleted)
                                             or admin.user.id in glovar.bot_ids)}
                save("admin_ids")
                text += f"{lang('status')}{lang('colon')}{code(lang('status_joined'))}\n"
            else:
                thread(leave_group, (client, gid))
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_left'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('reason_admin'))}\n")
        else:
            if gid in glovar.left_group_ids:
                return leave_group(client, gid)

            leave_group(client, gid)

            text += (f"{lang('status')}{lang('colon')}{code(lang('status_left'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('reason_unauthorized'))}\n")

        # Add inviter info
        if message.from_user.username:
            text += f"{lang('inviter')}{lang('colon')}{mention_id(inviter.id)}\n"
        else:
            text += f"{lang('inviter')}{lang('colon')}{code(inviter.id)}\n"

        # Send debug message
        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Init group error: {e}", exc_info=True)

    return False


@Client.on_message((Filters.incoming or glovar.aio) & Filters.channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix)
                   & exchange_channel)
def process_data(client: Client, message: Message) -> bool:
    # Process the data in exchange channel
    glovar.locks["receive"].acquire()
    try:
        data = receive_text_data(message)

        if not data:
            return True

        sender = data["from"]
        receivers = data["to"]
        action = data["action"]
        action_type = data["type"]
        data = data["data"]

        # This will look awkward,
        # seems like it can be simplified,
        # but this is to ensure that the permissions are clear,
        # so it is intentionally written like this
        if glovar.sender in receivers:

            if sender == "CAPTCHA":

                if action == "help":
                    if action_type == "welcome":
                        receive_help_welcome(client, data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "CLEAN":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "CONFIG":

                if action == "config":
                    if action_type == "commit":
                        receive_config_commit(data)
                    elif action_type == "reply":
                        receive_config_reply(client, data)

            elif sender == "LANG":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "LONG":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "MANAGE":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)

                elif action == "backup":
                    if action_type == "now":
                        thread(backup_files, (client,))
                    elif action_type == "rollback":
                        receive_rollback(client, message, data)

                elif action == "clear":
                    receive_clear_data(client, action_type, data)

                elif action == "config":
                    if action_type == "show":
                        receive_config_show(client, data)

                elif action == "leave":
                    if action_type == "approve":
                        receive_leave_approve(client, data)

                elif action == "remove":
                    if action_type == "bad":
                        receive_remove_bad(data)
                    elif action_type == "score":
                        receive_remove_score(data)
                    elif action_type == "watch":
                        receive_remove_watch(data)

                elif action == "update":
                    if action_type == "refresh":
                        receive_refresh(client, data)

            elif sender == "NOFLOOD":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "NOPORN":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "NOSPAM":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "RECHECK":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "REGEX":

                if action == "regex":
                    if action_type == "update":
                        receive_regex(client, message, data)
                    elif action_type == "count":
                        if data == "ask":
                            send_count(client)

            elif sender == "WARN":

                if action == "update":
                    if action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "WATCH":

                if action == "add":
                    if action_type == "watch":
                        receive_watch_user(data)

        return True
    except Exception as e:
        logger.warning(f"Process data error: {e}", exc_info=True)
    finally:
        glovar.locks["receive"].release()

    return False
