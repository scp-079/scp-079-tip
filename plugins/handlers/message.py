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

from pyrogram import Client, filters
from pyrogram.types import Message

from .. import glovar
from ..functions.channel import get_debug_text
from ..functions.etc import code, delay, general_link, get_now, lang, mention_id, thread
from ..functions.file import save
from ..functions.filters import (aio, authorized_group, declared_message, exchange_channel, from_user, hide_channel,
                                 is_declared_message, is_high_score_user, is_keyword_message, is_nospam_message,
                                 is_nospam_join, is_rm_text, is_user_class_d, is_watch_user, new_group, test_group)
from ..functions.group import leave_group, leave_unauthorized, join_hint, pin_cancel, pin_hold, save_admins
from ..functions.ids import init_group_id, init_user_id
from ..functions.receive import (receive_add_bad, receive_captcha_flood, receive_config_commit, receive_clear_data,
                                 receive_config_reply, receive_config_show, receive_declared_message, receive_group_id,
                                 receive_help_welcome, receive_ignore_ids, receive_leave_approve, receive_regex,
                                 receive_refresh, receive_remove_bad, receive_remove_score, receive_remove_watch,
                                 receive_remove_white, receive_white_users, receive_rollback, receive_text_data,
                                 receive_user_score, receive_watch_user)
from ..functions.telegram import get_admins, send_message
from ..functions.timers import backup_files, send_count
from ..functions.tip import tip_keyword, tip_rm, tip_welcome

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(filters.incoming & filters.group & ~filters.linked_channel & ~filters.service
                   & ~test_group & authorized_group
                   & from_user
                   & ~declared_message)
def check(client: Client, message: Message) -> bool:
    # Check the messages sent from groups
    result = False

    glovar.locks["message"].acquire()

    try:
        # Basic data
        gid = message.chat.id
        mid = message.message_id

        # Check the config
        if ((not glovar.configs[gid].get("keyword") and not glovar.configs[gid].get("rm"))
                or (not glovar.keywords[gid].get("kws") and not glovar.rms[gid].get("reply"))):
            return False

        # Check class D status
        if is_user_class_d(gid, message.from_user):
            return False

        # Check NOSPAM status
        if is_nospam_message(message):
            return False

        # Check declare status
        if is_declared_message(None, None, message):
            return True

        # Check keyword
        detection = is_keyword_message(message)

        if detection:
            key = detection["key"]
            glovar.keywords[gid]["kws"][key]["count"] += 1
            glovar.keywords[gid]["kws"][key]["today"] += 1
            save("keywords")
            return tip_keyword(client, message, detection)

        # Check rm
        detection = is_rm_text(message)

        if detection:
            glovar.rms[gid]["count"] += 1
            glovar.rms[gid]["today"] += 1
            save("rms")
            return tip_rm(client, gid, mid)

        result = True
    except Exception as e:
        logger.warning(f"Check error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


@Client.on_message(filters.incoming & filters.group & filters.new_chat_members
                   & ~test_group & ~new_group & authorized_group
                   & from_user
                   & ~declared_message)
def check_join(client: Client, message: Message) -> bool:
    # Check new joined user
    result = False

    glovar.locks["message"].acquire()

    try:
        # Basic data
        gid = message.chat.id
        user = message.new_chat_members[0]
        mid = message.message_id
        now = message.date or get_now()

        # Check class D status
        if is_user_class_d(gid, user):
            return False

        # Check NOSPAM status
        if is_nospam_join(client, gid, user):
            return False

        # Check declare status
        if is_declared_message(None, None, message):
            return False

        # Check keyword name
        detection = is_keyword_message(message)

        if detection:
            glovar.member_ids[gid].add(user.id)
            save("member_ids")
            return tip_keyword(client, message, detection)

        # Check config
        if not glovar.configs[gid].get("welcome"):
            return False

        # Work with CAPTCHA
        if glovar.configs[gid].get("captcha") and glovar.captcha_id in glovar.admin_ids[gid]:
            return False

        # Check group status
        if gid in glovar.flooded_ids:
            return False

        # Add to joined members
        glovar.member_ids[gid].add(user.id)
        save("member_ids")

        # User status
        if is_watch_user(user, "ban", now):
            return False

        if is_watch_user(user, "delete", now):
            return False

        if is_high_score_user(user):
            return False

        # Init the user's status
        if not init_user_id(user.id):
            return False

        # Welcome
        glovar.welcomes[gid]["count"] += 1
        glovar.welcomes[gid]["today"] += 1
        save("welcomes")
        tip_welcome(client, user, gid, mid)

        result = True
    except Exception as e:
        logger.warning(f"Check join error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


@Client.on_message((filters.incoming | aio) & filters.channel
                   & ~filters.command(glovar.all_commands, glovar.prefix)
                   & hide_channel, group=-1)
def exchange_emergency(client: Client, message: Message) -> bool:
    # Sent emergency channel transfer request
    result = False

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

        result = True
    except Exception as e:
        logger.warning(f"Exchange emergency error: {e}", exc_info=True)

    return result


@Client.on_message(filters.incoming & filters.group
                   & (filters.new_chat_members | filters.group_chat_created | filters.supergroup_chat_created)
                   & ~test_group & new_group
                   & from_user)
def init_group(client: Client, message: Message) -> bool:
    # Initiate new groups
    result = False

    glovar.locks["admin"].acquire()

    try:
        # Basic data
        gid = message.chat.id
        inviter = message.from_user

        # Text prefix
        text = get_debug_text(client, message.chat)

        # Check permission
        if inviter.id != glovar.user_id:
            return leave_unauthorized(client, message, text)

        # Remove the left status
        glovar.left_group_ids.discard(gid)
        save("left_group_ids")

        # Update group's admin list
        if not init_group_id(gid):
            return True

        # Get admins
        admin_members = get_admins(client, gid)

        if admin_members:
            save_admins(gid, admin_members)
            join_hint(client, gid)
            text += f"{lang('status')}{lang('colon')}{code(lang('status_joined'))}\n"
        else:
            leave_group(client, gid)
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_left'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('reason_admin'))}\n")

        # Add inviter info
        if inviter.username:
            text += f"{lang('inviter')}{lang('colon')}{mention_id(inviter.id)}\n"
        else:
            text += f"{lang('inviter')}{lang('colon')}{code(inviter.id)}\n"

        # Send debug message
        thread(send_message, (client, glovar.debug_channel_id, text))

        result = True
    except Exception as e:
        logger.warning(f"Init group error: {e}", exc_info=True)
    finally:
        glovar.locks["admin"].release()

    return result


@Client.on_message(filters.incoming & filters.group & filters.linked_channel
                   & authorized_group
                   & ~declared_message)
def pin_process(client: Client, message: Message) -> bool:
    # Process pinned message
    result = False

    glovar.locks["message"].acquire()

    try:
        # Basic data
        gid = message.chat.id

        # Check flood status
        if gid in glovar.flooded_ids:
            return False

        # Cancel the pinned message
        if glovar.configs[gid].get("cancel", False):
            return delay(3, pin_cancel, [client, gid])

        # Hold the pinned message
        hold = glovar.configs[gid].get("hold", False)
        mid = glovar.pinned_ids.get(gid, 0)

        # Check config
        if not hold or not mid:
            return False

        # Pin the message
        delay(3, pin_hold, [client, gid, mid])

        result = True
    except Exception as e:
        logger.warning(f"Pin process error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


@Client.on_message(filters.incoming & filters.group & ~filters.linked_channel
                   & authorized_group
                   & from_user
                   & ~declared_message)
def pin_record(_: Client, message: Message) -> bool:
    # Record pinned message
    result = False

    glovar.locks["message"].acquire()

    try:
        # Basic data
        gid = message.chat.id
        mid = message.message_id

        # Check flood status
        if gid in glovar.flooded_ids:
            return False

        # Check config
        if glovar.configs[gid].get("cancel", False) or glovar.configs[gid].get("hold", False):
            return False

        # Save message id
        glovar.pinned_ids[gid] = mid
        save("pinned_ids")

        result = True
    except Exception as e:
        logger.warning(f"Pin record error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


@Client.on_message((filters.incoming | aio) & filters.channel
                   & ~filters.command(glovar.all_commands, glovar.prefix)
                   & exchange_channel)
def process_data(client: Client, message: Message) -> bool:
    # Process the data in exchange channel
    result = False

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

            if sender == "AVATAR":

                if action == "add":
                    if action_type == "white":
                        receive_white_users(client, message)

                elif action == "remove":
                    if action_type == "white":
                        receive_remove_white(data)

            elif sender == "CAPTCHA":

                if action == "captcha":
                    if action_type == "flood":
                        receive_captcha_flood(data)

                elif action == "help":
                    if action_type == "welcome":
                        receive_help_welcome(client, data)

                elif action == "share":
                    if action_type == "group":
                        receive_group_id(data)

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

                elif action == "share":
                    if action_type == "group":
                        receive_group_id(data)

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
                    elif action_type == "ignore":
                        receive_ignore_ids(client, message, sender)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "REGEX":

                if action == "regex":
                    if action_type == "update":
                        receive_regex(client, message, data)
                    elif action_type == "count":
                        data == "ask" and send_count(client)

                elif action == "share":
                    if action_type == "group":
                        receive_group_id(data)

            elif sender == "TICKET":

                if action == "share":
                    if action_type == "group":
                        receive_group_id(data)

            elif sender == "USER":
                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(data)

                elif action == "update":
                    if action_type == "ignore":
                        receive_ignore_ids(client, message, sender)

            elif sender == "WARN":

                if action == "update":
                    if action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "WATCH":

                if action == "add":
                    if action_type == "watch":
                        receive_watch_user(data)

        result = True
    except Exception as e:
        logger.warning(f"Process data error: {e}", exc_info=True)
    finally:
        glovar.locks["receive"].release()

    return result
