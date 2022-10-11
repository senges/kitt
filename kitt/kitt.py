#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Author : @senges
# Version : See __version__.py
# Description : A portable shell
# =============================================================================


import click

from kitt.__version__ import __version__
from kitt.client import client
from kitt import logger


@click.group()
@click.help_option('-h', '--help')
@click.option('--debug', '-d', is_flag=True, help='Debug mode')
def main(debug):
    """main command group"""

    logger.config(debug)


@main.command('version')
def _version():
    """Show version"""

    logger.info('Kitt v' + __version__)


@main.command('run')
@click.help_option('-h', '--help')
@click.option('-v', '--volume', is_flag=False, multiple=True, help='Additional volume in OCI format')
@click.option('-u', '--user', is_flag=False, help='Run as other host user')
@click.option('--dind', is_flag=True, help='Enable docker in docker')
@click.argument('name', type=click.STRING)
def _run(name, volume, user, dind):
    """Run kitt shell"""

    extras = {
        "volumes": volume,
        "run_as": user,
        "dind": dind,
    }

    client.run(name, extras)


@main.command('list')
@click.help_option('-h', '--help')
def _list():
    """List local images"""

    client.list()


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
@click.argument('config', type=click.STRING)
@click.argument('name', type=click.STRING)
def _build(config, name):
    """Build image from source config file"""

    client.build(name, config)


@main.command('pull')
@click.help_option('-h', '--help')
@click.argument('registry', type=click.STRING)
@click.argument('name', type=click.STRING)
def _pull(registry, name):
    """Pull image and exit"""

    client.pull(registry, name)


@main.command('push')
@click.help_option('-h', '--help')
@click.argument('registry', type=click.STRING)
@click.argument('name', type=click.STRING)
def _push(registry, name):
    """Push kitt image to registry"""

    client.push(registry, name)


@main.command('inspect')
@click.help_option('-h', '--help')
@click.argument('image', type=click.STRING)
def _inspect(image):
    """Show image metadata"""

    client.inspect(image)


@main.command('patch')
@click.help_option('-h', '--help')
@click.argument('image', type=click.STRING)
def _patch(image):
    """Patch image runtime metadata"""

    client.patch(image)


if __name__ == '__main__':
    main(False)
