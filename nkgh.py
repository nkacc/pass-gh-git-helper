#!/usr/bin/env python3

"""Implementation of logic related to NK's GH cli.

.. codeauthor:: Naveen S R
"""


import platform
import configparser
import logging
from pathlib import Path
from typing import Mapping


LOGGER = logging.getLogger(__name__)
if platform.system() == "Windows": # probably work PC/Lap
    GITHUBCLI_DIR = r"Dev\bin\scoop\persist-in-windows\others\GitHubCLI"
    GITHUBCLI_DIR = Path.expanduser(Path(r"~\nk")) / GITHUBCLI_DIR
elif platform.system() == "Linux": # Primary
    GITHUBCLI_DIR = None
    #Yet2Decide
else:
    GITHUBCLI_DIR = None


def get_password(
    target: str, section: configparser.SectionProxy, request: Mapping[str, str]
) -> bool:
    pass
