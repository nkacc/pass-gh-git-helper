#!/usr/bin/env python3

"""Implementation of logic related to NK's GH cli.

.. codeauthor:: Naveen S R
"""


import platform
import subprocess
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
    """Resolve the given credential request using GH cli.

    The result is printed automatically.

    Args:
        target:
            The config dir of gh cli to use as a string.
        section:
            The matched mapping section as a ConfigParser.SectionProxy instance.
        request:
            The credential request specified as a dict of key-value pairs.

    Returns:
        The success status as a bool.
    """
    if "protocol" not in request or request["protocol"] != "https":
        return False # gh helper only respond for https

    if target.lower() in ("og", "orginal"):
        target = None # Let gh figure it out
    elif target == "" or target.lower() == "default":
        target = str(GITHUBCLI_DIR / "config")
    else:
        target = str(GITHUBCLI_DIR / target)

    gh_cli = str(Path.home()) + r"\nk\Dev\bin\scoop\dir\apps\gh\current\bin\gh.exe"
    environment = {
        "GH_PATH" : gh_cli,
        "GH_DEBUG" : "no"
    }
    if target:
        environment["GH_CONFIG_DIR"] = target

    request_text = "protocol={protocol}\nhost={host}\n"
    request_text += ("username={username}\n" if "username" in request else "")
    request_text = request_text.format(
        protocol=request["protocol"],
        host=request["host"],
        username=request.get("username")
    )
    process = subprocess.run(
        [gh_cli, "auth", "git-credential", "get"],
        input=request_text, text=True, capture_output=True, env=environment
    )

    response = None
    success_flag = False
    if process.returncode == 0:
        response = dict(
            x.split("=", 1) for x in process.stdout.splitlines()
        )
        success_flag = bool(
            "password" in response and response["password"]
            and "username" in response and response["username"]
            and response["username"] not in ("x-access-token", "NotDeclaredHere")
            and (
                ("username" in request and request["username"] == response["username"])
                or ("username" not in request
                    and section.get("gh_username") is not None
                        and section.get("gh_username") == response["username"])
                or ("username" not in request and section.get("gh_username") is None)
            )
        )

    if not success_flag:
        environment.pop("GH_CONFIG_DIR", None) # og gh is enough

        if "username" in request:
            username = request["username"]
        elif section.get("gh_username"):
            # if username not in request use from mapping file
            username = section.get("gh_username")
        else:
            username = None # Yet2Decide

        process = subprocess.run(
            [gh_cli, "auth", "token", "-h", request["host"], "-u", username],
            text=True, capture_output=True, env=environment
        )
        if process.returncode == 0:
            response = {
                "username" : username,
                "password" : process.stdout.strip()
            }
            success_flag = True

    if success_flag:
        print("password={password}".format(password=response["password"]))  # noqa: T201
        if "username" not in request:
            print("username={username}".format(username=response["username"]))  # noqa: T201

        return True # Success
    else:
        return False # Failed
