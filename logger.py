from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

# Display cli success
def success(msg: str):
    console.print('[green]✓ ' + msg)

# Display cli info
def info(msg: str):
    console.print('[yellow]~ ' + msg)

# Provide pending status object
def waiter(msg: str):
    return console.status('[bold grey]' + msg)

# Program panic
def panic(err: str):
    console.print('[red]✗ ' + err)
    exit(1)