"""Logging and debugging utilities"""

import traceback

from typing import Union

from rich.console import Console

console = Console()
console.debug = False


def success(msg: str):
    """Display cli success

    Args:
        msg (str): success message
    """
    console.print('[green]✓ ' + msg)


def info(msg: str):
    """Display cli info

    Args:
        msg (str): info message
    """
    console.print('[sky_blue3] ' + msg)


def warning(msg: str):
    """Display cli warning

    Args:
        msg (str): warning message
    """
    console.print('[yellow]~ ' + msg)


def waiter(msg: str):
    """Provide pending status object

    Args:
        msg (str): waiter message
    """
    return console.status('[bold grey]' + msg)


def debug(msg: Union[str, Exception]):
    """Extended log for debug mode

    Args:
        msg (Union[str, Exception]): debug data to log
    """
    if console.debug:
        if not isinstance(msg, str):
            console.log('[grey62]' + str(traceback.format_exc()))
        console.log('[grey62]' + str(msg))


def config(debug_mode: bool = False):
    """Config logger

    Args:
        debug_mode (bool, optional): set debug mode. Defaults to False.
    """
    console.debug = debug_mode


def panic(msg: str):
    """Program panic

    Args:
        msg (str): panic message
    """
    console.print('[red]✗ ' + msg)
    exit(1)
