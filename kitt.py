#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Author : @senges
# Version : March 2022
# Description : A portable toolbox
# =============================================================================

import click
import logger

from container import client as docker

@click.group()
@click.help_option('-h', '--help')
@click.option('-d', '--debug', is_flag = True, help = 'Debug mode')
def main(debug):
    logger.config(debug)
    pass

@main.command('run')
@click.help_option('-h', '--help')
@click.option('-p', '--pull', is_flag = True, help = 'Pull image if not present')
@click.option('-v', '--volume', is_flag = False, multiple = True, help = 'Additional volume in docker format')
@click.argument('name', type = click.STRING)
def _run(name, pull, volume):
    """Run environment"""

    if pull:
        docker.pull(name)
    
    docker.run(name)

@main.command('pull')
@click.help_option('-h', '--help')
@click.argument('name')
def _pull(name):
    """Pull image and exit"""

    docker.pull(name)
    
@main.command('list')
@click.help_option('-h', '--help')
def _list():
    """List local images"""

    for image in docker.images():
        logger.info(' '.join(image.tags))

@main.command('refresh')
@click.help_option('-h', '--help')
def _refresh():
    """Pull latest version of local images"""

    docker.refresh()

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

    docker.build(file, catalog)

if __name__ == '__main__':
    main()