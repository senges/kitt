#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Author : @senges
# Version : See __version__.py
# Description : A portable shell
# =============================================================================

from . __version__ import __version__

import os
import click

from . container import client
from . import logger


@click.group()
@click.help_option('-h', '--help')
@click.option('--debug', '-d', is_flag=True, help='Debug mode')
def main(debug):
    logger.config(debug)


@main.command('version')
def _version():
    """Show version"""

    logger.info('Kitt v' + __version__)


@main.command('run')
@click.help_option('-h', '--help')
@click.option('-v', '--volume', is_flag=False, multiple=True, help='Additional volume in OCI format')
@click.argument('name', type=click.STRING)
def _run(name, volume):
    """Run kitt shell"""

    extras = {
        "volumes": volume
    }

    client.run(name, extras)


@main.command('list')
@click.help_option('-h', '--help')
def _list():
    """List local images"""

    for image in client.images():
        basename = [x[5:] for x in image.tags if x.startswith('kitt:')].pop()
        logger.info('➜ ' + basename)


@main.command('remove')
@click.help_option('-h', '--help')
@click.argument("name")
def _remove(name):
    """Remove local image"""

    client.remove(name)


@main.command('prune')
@click.help_option('-h', '--help')
def _prune():
    """Prune local images"""

    client.prune()


@main.command('refresh')
@click.help_option('-h', '--help')
def _refresh():
    """Pull latest version of local images"""

    client.refresh()


@main.command('build')
@click.help_option('-h', '--help')
@click.option('-f', '--file', is_flag=False, multiple=False, help='Input kitt file')
@click.option('-c', '--catalog', is_flag=False, multiple=True, help='Input Catalog file')
@click.argument('name', type=click.STRING)
def _build(name, file, catalog):
    """Build image from source config file"""

    client.build(name, file, catalog)


@main.command('pull')
@click.help_option('-h', '--help')
@click.argument('url', type=click.STRING)
@click.argument('name', type=click.STRING)
def _pull(url, name):
    """Pull image and exit"""

    client.pull(url, name)


@main.command('push')
@click.help_option('-h', '--help')
@click.option('-r', '--registry', prompt=True, is_flag=False, multiple=False, help='Registry URL')
@click.argument('image', type=click.STRING)
def _push(registry, image):
    """Push image to registry"""

    client.push(registry, image)


@main.command('patch')
@click.help_option('-h', '--help')
@click.argument('image', type=click.STRING)
def _patch(image):
    """Patch image runtime metadata"""

    client.patch(image)

@main.command('inspect')
@click.help_option('-h', '--help')
@click.argument('image', type=click.STRING)
def _inspect(image):
    """Show image metadata"""

    client.inspect(image)


if __name__ == '__main__':
    main()
