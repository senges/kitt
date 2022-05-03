#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Author : @senges
# Version : March 2022
# Description : A portable toolbox
# =============================================================================

import os
import click
import logger

from container import client

@click.group()
@click.help_option('-h', '--help')
@click.option('--debug', is_flag = True, help = 'Debug mode')
# @click.option('--driver', default = 'podman', type = click.Choice(['podman', 'docker']))
def main(debug):
    logger.config(debug)

@main.command('run')
@click.help_option('-h', '--help')
@click.option('-p', '--pull', is_flag = True, help = 'Pull image if not present')
@click.option('-v', '--volume', is_flag = False, multiple = True, help = 'Additional volume in OCI format')
@click.argument('name', type = click.STRING)
def _run(name, pull, volume):
    """Run environment"""

    if pull:
        client.pull(name)
    
    client.run(name)

@main.command('pull')
@click.help_option('-h', '--help')
@click.argument('name')
def _pull(name):
    """Pull image and exit"""

    client.pull(name)
    
@main.command('list')
@click.help_option('-h', '--help')
def _list():
    """List local images"""

    for image in client.images():
        basenames = map(lambda x: os.path.basename(x), image.tags)
        logger.info(' '.join(basenames))

@main.command('refresh')
@click.help_option('-h', '--help')
def _refresh():
    """Pull latest version of local images"""

    client.refresh()

@main.command('config')
@click.help_option('-h', '--help')
@click.confirmation_option(prompt = 'Operation will remove any previous config file. Continue ?')
def _config():
    """Configure kitt"""

    pass

@main.command('build')
@click.help_option('-h', '--help')
@click.option('-f', '--file', is_flag = False, multiple = False, help = 'Input kitt file')
@click.option('-c', '--catalog', is_flag = False, multiple = True, help = 'Input Catalog file')
def _build(file, catalog):
    """Build images from source"""

    client.build(file, catalog)

if __name__ == '__main__':
    main()