# SCP-079-TIP

This bot is used to send tips.

## How to use

- [Demo](https://t.me/SCP_079_TIP_BOT)
- Read [the document](https://scp-079.org/tip/) to learn more
- [README](https://scp-079.org/readme/) of the SCP-079 Project's demo bots
- Discuss [group](https://t.me/SCP_079_CHAT)

## Requirements

- Python 3.6 or higher
- Debian 10: `sudo apt update && sudo apt install opencc pybind11-dev -y`
- [Google RE2](https://github.com/google/re2) installed
    - `git clone `
- pip: `pip install -r requirements.txt`

## Files

- examples
   - `config.ini` -> `../data/config/config.ini` : Configuration example
   - `join.txt` -> `../data/config/join.txt` : Join template example
   - `start.txt` -> `../data/config/start.txt` : Start template example
- plugins
    - functions
        - `channel.py` : Functions about channel
        - `command.py` : Functions about command
        - `config.py` : Functions about group settings
        - `decorators.py` : Some decorators
        - `etc.py` : Miscellaneous
        - `file.py` : Save files
        - `filters.py` : Some filters
        - `group.py` : Functions about group
        - `ids.py` : Modify id lists
        - `markup.py` : Get reply markup
        - `program.py` : Functions about program
        - `receive.py` : Receive data from exchange channel
        - `telegram.py` : Some telegram functions
        - `timers.py` : Timer functions
        - `tip.py` : Functions about tips
        - `user.py` : Functions about user and channel object
    - handlers
        - `callback.py` : Handle callbacks
        - `command.py` : Handle commands
        - `message.py`: Handle messages
    - `checker.py` : Check the format of `config.ini`
    - `glovar.py` : Global variables
    - `start.py` : Execute before client start
    - `version.py` : Execute before main script start
- `.gitignore` : Ignore
- `Dockerfile` : Assemble the docker image
- `LICENSE` : GPLv3
- `main.py` : Start here
- `README.md` : This file
- `requirements.txt` : Managed by pip

## Contribution

Contributions are always welcome, whether it's modifying source code to add new features or bug fixes, documenting new file formats or simply editing some grammar.

You can also join the [discuss group](https://t.me/SCP_079_CHAT) if you are unsure of anything.

## Translation

- [Choose Language Tags](https://www.w3.org/International/questions/qa-choosing-language-tags)
- [Language Subtag Registry](https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry)

## License

Licensed under the terms of the [GNU General Public License v3](LICENSE).
