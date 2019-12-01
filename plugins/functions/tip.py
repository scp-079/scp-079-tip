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
