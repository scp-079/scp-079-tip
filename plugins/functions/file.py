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
from os import remove
from os.path import exists
from pickle import dump
from shutil import copyfile, move
from typing import Any

from pyAesCrypt import decryptFile, encryptFile
from pyrogram import Client

from .. import glovar
from .decorators import threaded
from .etc import random_str
from .telegram import download_media

# Enable logging
logger = logging.getLogger(__name__)


def crypt_file(operation: str, file_in: str, file_out: str) -> bool:
    # Encrypt or decrypt a file
    result = False

    try:
        if not file_in or not file_out:
            return False

        buffer = 64 * 1024

        if operation == "decrypt":
            decryptFile(file_in, file_out, glovar.password, buffer)
        else:
            encryptFile(file_in, file_out, glovar.password, buffer)

        result = True
    except Exception as e:
        logger.warning(f"Crypt file error: {e}", exc_info=True)

    return result


def data_to_file(data: Any) -> str:
    # Save data to a file in tmp directory
    result = ""

    try:
        file_path = get_new_path()

        with open(file_path, "wb") as f:
            dump(data, f)

        result = file_path
    except Exception as e:
        logger.warning(f"Data to file error: {e}", exc_info=True)

    return result


def delete_file(path: str) -> bool:
    # Delete a file
    result = False

    try:
        if not(path and exists(path)):
            return False

        result = remove(path) or True
    except Exception as e:
        logger.warning(f"Delete file error: {e}", exc_info=True)

    return result


def file_txt(text: str) -> str:
    # Generate a TXT file
    result = ""

    try:
        file = get_new_path(".txt")

        with open(file, "w") as f:
            f.write(text)

        result = file
    except Exception as e:
        logger.warning(f"File txt error: {e}", exc_info=True)

    return result


def get_downloaded_path(client: Client, file_id: str, file_ref: str) -> str:
    # Download file, get it's path on local machine
    result = ""

    try:
        if not file_id:
            return ""

        file_path = get_new_path()
        result = download_media(client, file_id, file_ref, file_path)
    except Exception as e:
        logger.warning(f"Get downloaded path error: {e}", exc_info=True)

    return result


def get_new_path(extension: str = "", prefix: str = "") -> str:
    # Get a new path in tmp directory
    result = ""

    try:
        file_path = random_str(8)

        while exists(f"{glovar.TMP_PATH}/{prefix}{file_path}{extension}"):
            file_path = random_str(8)

        result = f"{glovar.TMP_PATH}/{prefix}{file_path}{extension}"
    except Exception as e:
        logger.warning(f"Get new path error: {e}", exc_info=True)

    return result


def move_file(src: str, dst: str) -> bool:
    # Move a file
    result = False

    try:
        if not src or not exists(src) or not dst:
            return False

        result = bool(move(src, dst))
    except Exception as e:
        logger.warning(f"Move file error: {e}", exc_info=True)

    return result


@threaded(daemon=False)
def save(file: str) -> bool:
    # Save a global variable to a file
    result = False

    try:
        if not glovar:
            return False

        with open(f"{glovar.PICKLE_BACKUP_PATH}/{file}", "wb") as f:
            dump(eval(f"glovar.{file}"), f)

        result = copyfile(f"{glovar.PICKLE_BACKUP_PATH}/{file}", f"{glovar.PICKLE_PATH}/{file}")
    except Exception as e:
        logger.warning(f"Save error: {e}", exc_info=True)

    return result


def save_regex_timeout(word: str) -> bool:
    # Use this function to save removed regex
    result = False

    glovar.locks["regex"].acquire()

    try:
        glovar.timeout_words.add(word)
        save("timeout_words")
        result = True
    except Exception as e:
        logger.warning(f"Save regex timeout error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return result
