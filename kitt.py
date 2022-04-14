#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Author : @senges
# Version : March 2022
# Description : A portable toolbox
# =============================================================================

import click

from container import client as docker

@click.group()
@click.help_option('-h', '--help')
def main():
    pass

@main.command('run')
@click.help_option('-h', '--help')
@click.option('-p', '--pull', is_flag = True, help = 'Pull image if not present')
@click.option('-v', '--volume', is_flag = False, multiple = True, help = 'Additional volume in docker format')
@click.argument('name', type = click.STRING)
def _run(name, pull, volume):
    """Run environment"""

    pass

@main.command('pull')
@click.help_option('-h', '--help')
@click.argument('name')
def _pull(name):
    """Pull image and exit"""

    pass
    
@main.command('list')
@click.help_option('-h', '--help')
def _list():
    """List local images"""

    pass

@main.command('refresh')
@click.help_option('-h', '--help')
def _refresh():
    """Pull latest version of local images"""

    pass

@main.command('config')
@click.help_option('-h', '--help')
@click.confirmation_option(prompt = 'Operation will remove any previous config file. Continue ?')
def _config():
    """Configure kitt"""

    pass

@main.command('build')
@click.help_option('-h', '--help')
def _build():
    """Build images from source"""

    pass

if __name__ == '__main__':
    main()