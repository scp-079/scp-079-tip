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
from copy import deepcopy

from .. import glovar
from .file import save

# Enable logging
logger = logging.getLogger(__name__)


def init_group_id(gid: int) -> bool:
    # Init group data
    result = False

    try:
        if gid == glovar.test_group_id:
            return False

        if gid in glovar.left_group_ids:
            return False

        if glovar.aio and any(gid == glovar.group_ids[group] for group in glovar.group_ids):
            return False

        if glovar.admin_ids.get(gid) is None:
            glovar.admin_ids[gid] = set()
            save("admin_ids")

        if glovar.member_ids.get(gid) is None:
            glovar.member_ids[gid] = set()
            save("member_ids")

        if glovar.message_ids.get(gid) is None:
            glovar.message_ids[gid] = deepcopy(glovar.default_message_data)
            save("message_ids")

        if glovar.trust_ids.get(gid) is None:
            glovar.trust_ids[gid] = set()
            save("trust_ids")

        if glovar.channels.get(gid) is None:
            glovar.channels[gid] = deepcopy(glovar.default_channel_data)
            save("channels")

        if glovar.configs.get(gid) is None:
            glovar.configs[gid] = deepcopy(glovar.default_config)
            save("configs")

        if glovar.keywords.get(gid) is None:
            glovar.keywords[gid] = deepcopy(glovar.default_keyword_data)
            save("keywords")

        if glovar.ots.get(gid) is None:
            glovar.ots[gid] = deepcopy(glovar.default_ot_data)
            save("ots")

        if glovar.rms.get(gid) is None:
            glovar.rms[gid] = deepcopy(glovar.default_rm_data)
            save("rms")

        if glovar.welcomes.get(gid) is None:
            glovar.welcomes[gid] = deepcopy(glovar.default_welcome_data)
            save("welcomes")

        if glovar.declared_message_ids.get(gid) is None:
            glovar.declared_message_ids[gid] = set()

        if glovar.keyworded_ids.get(gid) is None:
            glovar.keyworded_ids[gid] = {}

        if glovar.members.get(gid) is None:
            glovar.members[gid] = {}

        if glovar.welcomed_ids.get(gid) is None:
            glovar.welcomed_ids[gid] = set()

        result = True
    except Exception as e:
        logger.warning(f"Init group id {gid} error: {e}", exc_info=True)

    return result


def init_user_id(uid: int) -> bool:
    # Init user data
    result = False

    try:
        if glovar.user_ids.get(uid) is not None:
            return True

        glovar.user_ids[uid] = deepcopy(glovar.default_user_status)
        save("user_ids")

        result = True
    except Exception as e:
        logger.warning(f"Init user id {uid} error: {e}", exc_info=True)

    return result
