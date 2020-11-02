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
from subprocess import run
from time import sleep

from pyrogram import Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .. import glovar
from .channel import share_data, share_regex_count
from .decorators import threaded
from .etc import bold, code, general_link, get_now, get_readable_time, lang, thread
from .file import data_to_file, move_file, save
from .group import delete_message, get_pinned, leave_group, save_admins
from .telegram import get_admins, get_chat_member, get_group_info, get_members, get_messages, send_message
from .tip import get_invite_link

# Enable logging
logger = logging.getLogger(__name__)


@threaded()
def backup_files(client: Client) -> bool:
    # Backup data files to BACKUP
    result = False

    try:
        for file in glovar.file_list:
            # Check
            if not eval(f"glovar.{file}"):
                continue

            # Share
            share_data(
                client=client,
                receivers=["BACKUP"],
                action="backup",
                action_type="data",
                data=file,
                file=f"{glovar.PICKLE_PATH}/{file}"
            )
            sleep(5)

        result = True
    except Exception as e:
        logger.warning(f"Backup error: {e}", exc_info=True)

    return result


def interval_min_01(client: Client) -> bool:
    # Execute every minute
    result = True

    glovar.locks["message"].acquire()

    try:
        # Basic data
        now = get_now()

        # Delete tips
        for gid in list(glovar.message_ids):
            # Check clean mode config
            if not glovar.configs[gid].get("clean", True):
                continue

            # Destruct keywords messages
            for key in list(glovar.message_ids[gid]["keywords"]):
                mid, time = glovar.message_ids[gid]["keywords"][key]
                keyword = glovar.keywords[gid]["kws"].get(key, {})

                if not keyword:
                    glovar.message_ids[gid]["keywords"].pop(key, (0, 0))
                    delete_message(client, gid, mid)
                    continue

                destruct = glovar.keywords[gid]["kws"][key]["destruct"]

                if now - time < destruct:
                    continue

                glovar.message_ids[gid]["keywords"][key] = (0, 0)
                delete_message(client, gid, mid)

            # Destruct ot, rm, welcome message
            for the_type in ["ot", "rm", "welcome"]:
                mid, time = glovar.message_ids[gid][the_type]

                if not mid:
                    continue

                if now - time < eval(f"glovar.time_{the_type}"):
                    continue

                glovar.message_ids[gid][the_type] = (0, 0)
                delete_message(client, gid, mid)

        save("message_ids")

        # Generate a new invite link
        for gid in list(glovar.configs):
            if not glovar.configs[gid].get("channel", False):
                continue

            thread(get_invite_link, (client, "edit", gid), daemon=False)

        result = True
    except Exception as e:
        logger.warning(f"Interval min 01 error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


def interval_min_10() -> bool:
    # Execute every 10 minutes
    result = False

    glovar.locks["message"].acquire()
    
    try:
        # Clear keyworded users
        for gid in list(glovar.keyworded_ids):
            glovar.keyworded_ids[gid] = {}

        result = True
    except Exception as e:
        logger.warning(f"Interval min 10 error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


def log_rotation() -> bool:
    # Log rotation
    result = False

    try:
        move_file(f"{glovar.LOG_PATH}/log", f"{glovar.LOG_PATH}/log-{get_readable_time(the_format='%Y%m%d')}")

        with open(f"{glovar.LOG_PATH}/log", "w", encoding="utf-8") as f:
            f.write("")

        # Reconfigure the logger
        [logging.root.removeHandler(handler) for handler in logging.root.handlers[:]]
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.WARNING,
            filename=f"{glovar.LOG_PATH}/log",
            filemode="a"
        )

        run(f"find {glovar.LOG_PATH}/log-* -mtime +30 -delete", shell=True)

        result = True
    except Exception as e:
        logger.warning(f"Log rotation error: {e}", exc_info=True)

    return result


def resend_link(client: Client) -> bool:
    # Resend the invite link
    result = False

    glovar.locks["message"].acquire()

    try:
        # Proceed
        for gid in list(glovar.configs):
            if not glovar.configs[gid].get("resend", False):
                continue

            get_invite_link(
                client=client,
                the_type="send",
                gid=gid
            )

        result = True
    except Exception as e:
        logger.warning(f"Resend link error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


def reset_count() -> bool:
    # Reset count data
    result = False

    glovar.locks["message"].acquire()

    try:
        # Keywords
        for gid in list(glovar.keywords):
            for key in list(glovar.keywords[gid]["kws"]):
                glovar.keywords[gid]["kws"][key]["today"] = 0

        save("keywords")

        # RM
        for gid in list(glovar.rms):
            glovar.rms[gid]["today"] = 0

        save("rms")

        # Welcome
        for gid in list(glovar.welcomes):
            glovar.welcomes[gid]["today"] = 0

        save("welcomes")

        result = True
    except Exception as e:
        logger.warning(f"Reset count error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


def reset_data(client: Client) -> bool:
    # Reset user data every month
    result = False

    glovar.locks["message"].acquire()

    try:
        glovar.bad_ids = {
            "channels": set(),
            "users": set()
        }
        save("bad_ids")

        glovar.left_group_ids = set()
        save("left_group_ids")

        glovar.user_ids = {}
        save("user_ids")

        glovar.watch_ids = {
            "ban": {},
            "delete": {}
        }
        save("watch_ids")

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('reset'))}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))

        result = True
    except Exception as e:
        logger.warning(f"Reset data error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


def send_count(client: Client) -> bool:
    # Send regex count to REGEX
    result = False

    glovar.locks["regex"].acquire()

    try:
        for word_type in glovar.regex:
            share_regex_count(client, word_type)
            word_list = list(eval(f"glovar.{word_type}_words"))

            for word in word_list:
                eval(f"glovar.{word_type}_words")[word] = 0

            save(f"{word_type}_words")

        result = True
    except Exception as e:
        logger.warning(f"Send count error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return result


def share_regex_timeout(client: Client) -> bool:
    # Use this function to share regex remove request to REGEX
    result = False

    glovar.locks["regex"].acquire()

    try:
        if not glovar.timeout_words:
            return False

        file = data_to_file(glovar.timeout_words)
        save("timeout_words")
        result = share_data(
            client=client,
            receivers=["REGEX"],
            action="regex",
            action_type="timeout",
            file=file
        )
    except Exception as e:
        logger.warning(f"Share regex timeout error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return result


def update_admins(client: Client) -> bool:
    # Update admin list every day
    result = False

    glovar.locks["admin"].acquire()

    try:
        # Basic data
        group_list = list(glovar.admin_ids)

        # Check groups
        for gid in group_list:
            group_name, group_link = get_group_info(client, gid)
            admin_members = get_admins(client, gid)

            # Bot is not in the chat, leave automatically without approve
            if admin_members is False or any(admin.user.is_self for admin in admin_members) is False:
                leave_group(client, gid)
                share_data(
                    client=client,
                    receivers=["MANAGE"],
                    action="leave",
                    action_type="info",
                    data={
                        "group_id": gid,
                        "group_name": group_name,
                        "group_link": group_link
                    }
                )
                project_text = general_link(glovar.project_name, glovar.project_link)
                debug_text = (f"{lang('project')}{lang('colon')}{project_text}\n"
                              f"{lang('group_name')}{lang('colon')}{general_link(group_name, group_link)}\n"
                              f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                              f"{lang('status')}{lang('colon')}{code(lang('leave_auto'))}\n"
                              f"{lang('reason')}{lang('colon')}{code(lang('reason_leave'))}\n")
                thread(send_message, (client, glovar.debug_channel_id, debug_text))
                continue

            # Check the admin list
            if not (admin_members and any([admin.user.is_self for admin in admin_members])):
                continue

            # Save the admin list
            save_admins(gid, admin_members)

            # Check the permissions
            if glovar.user_id not in glovar.admin_ids[gid]:
                reason = "user"
            elif any(admin.user.is_self
                     and admin.can_delete_messages
                     and admin.can_restrict_members
                     and admin.can_invite_users
                     and admin.can_pin_messages
                     for admin in admin_members):
                glovar.lack_group_ids.discard(gid)
                save("lack_group_ids")
                continue
            elif gid in glovar.lack_group_ids:
                continue
            else:
                reason = "permissions"
                glovar.lack_group_ids.add(gid)
                save("lack_group_ids")

            # Send the leave request
            share_data(
                client=client,
                receivers=["MANAGE"],
                action="leave",
                action_type="request",
                data={
                    "group_id": gid,
                    "group_name": group_name,
                    "group_link": group_link,
                    "reason": reason
                }
            )

            # Send the info message to the group
            member = get_chat_member(client, gid, glovar.user_id)

            if reason == "user" and member and member.status not in {"restricted", "left", "kicked"}:
                continue

            info_text = f"{bold(lang('warning'))}{lang('colon')}{code(lang(f'warning_leave_{reason}'))}"
            markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=lang("read_manual"),
                            url=glovar.manual_link
                        )
                    ]
                ]
            )
            thread(send_message, (client, gid, info_text, None, markup))

            # Send the debug message
            reason = lang(f"reason_{reason}")
            project_link = general_link(glovar.project_name, glovar.project_link)
            debug_text = (f"{lang('project')}{lang('colon')}{project_link}\n"
                          f"{lang('group_name')}{lang('colon')}{general_link(group_name, group_link)}\n"
                          f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                          f"{lang('status')}{lang('colon')}{code(reason)}\n")
            thread(send_message, (client, glovar.debug_channel_id, debug_text))

        result = True
    except Exception as e:
        logger.warning(f"Update admin error: {e}", exc_info=True)
    finally:
        glovar.locks["admin"].release()

    return result


def update_members(client: Client) -> bool:
    # Update members ids of groups
    result = False

    try:
        for gid in list(glovar.message_ids):
            try:
                # Loop group members
                members = get_members(client, gid)

                # Check members
                if not members:
                    continue

                # Get member ids
                member_ids = {member.user.id for member in members}

                # Check member ids
                if not member_ids:
                    continue

                # Save member ids
                with glovar.locks["message"]:
                    glovar.member_ids[gid] = member_ids

                save("member_ids")
            except Exception as e:
                logger.warning(f"Update members in {gid} error: {e}", exc_info=True)

        result = True
    except Exception as e:
        logger.warning(f"Update members error: {e}", exc_info=True)

    return result


def update_pins(client: Client) -> bool:
    # Update pinned messages in groups
    result = False

    try:
        for gid in list(glovar.pinned_ids):
            # Check flood status
            if gid in glovar.flooded_ids:
                continue

            # Get old message
            oid = glovar.pinned_ids.get(gid, 0)

            if oid:
                old_message = get_messages(client, gid, oid)
            else:
                old_message = None

            print(old_message)

            # Check config
            if glovar.configs[gid].get("cancel", False) or (old_message and glovar.configs[gid].get("hold", False)):
                continue

            # Get pinned message
            pinned_message = get_pinned(client, gid, False)

            # Check pinned message
            if not pinned_message or (pinned_message.from_user and pinned_message.from_user.id in glovar.bot_ids):
                continue

            # Save pinned message
            glovar.pinned_ids[gid] = pinned_message.message_id
            save("pinned_ids")

        result = True
    except Exception as e:
        logger.warning(f"Update pins error: {e}", exc_info=True)

    return result


def update_status(client: Client, the_type: str) -> bool:
    # Update running status to BACKUP
    result = False

    try:
        result = share_data(
            client=client,
            receivers=["BACKUP"],
            action="backup",
            action_type="status",
            data={
                "type": the_type,
                "backup": glovar.backup
            }
        )
    except Exception as e:
        logger.warning(f"Update status error: {e}", exc_info=True)

    return result
