import traceback

from typing import Union

from rich.console import Console, Capture
from rich.table import Table
from rich import box

console = Console()
console.debug = False

# Display cli success
def success(msg: str):
    console.print('[green]✓ ' + msg)

# Display cli info
def info(msg: str):
    console.print('[sky_blue3] ' + msg)

# Display cli info
def warning(msg: str):
    console.print('[yellow]~ ' + msg)

# Provide pending status object
def waiter(msg: str):
    return console.status('[bold grey]' + msg)

# Extended log for debug mode
def debug(msg: Union[str, Exception]):
    if console.debug:
        if not isinstance(msg, str):
            console.log('[grey62]' + str(traceback.format_exc()))
        console.log('[grey62]' + str(msg))

# Config logger
def config(debug: bool = False):
    console.debug = debug

# Program panic
def panic(err: str):
    console.print('[red]✗ ' + err)
    exit(1)