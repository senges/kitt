"""Kitt commands handler - Core module"""

import os
import grp
import uuid
import json
import tempfile
import subprocess

from typing import Tuple
from pwd import getpwnam

from fs.tempfs import TempFS, errors as TempFSErrors

from kitt import plugins
from kitt.__version__ import __version__
from kitt.config import ConfigUtils
from kitt.images import DockerImageManager, Composer
from kitt.crypto import b64d, uncipher_vault, secure_prompt
from kitt import logger
from kitt.logger import (
    success,
    info,
    warning,
    waiter,
    panic,
)


class KittClient:
    """Kitt Client"""

    def __init__(self):
        template = ConfigUtils.mkpath('static/Dockerfile.j2')
        self.image_composer = Composer(template)
        self.image_manager = DockerImageManager(logger)

    def run(self, name: str, extras: dict = None):
        """Run kitt shell

        Args:
            name (str): kitt image specifier
            extras (dict, optional): extras runtime configurations. Defaults to None.
        """
        if not self.image_manager.stat('kitt', name):
            panic(f'Image { name } not found. Use `pull` command first.')

        env = []
        groups = []

        user_uid = os.getuid()
        user_gid = os.getuid()
        user_home = os.environ.get('HOME')

        extras = extras or {}

        if username := extras.get('run_as'):
            try:
                user = getpwnam(username)
                user_uid = user.pw_uid
                user_gid = user.pw_gid
            except KeyError:
                panic(f'Could not get "{ username }" user infos')

        config = self._config(name)
        hostname = config.get('hostname', 'kitt')

        if config.get('dind') or extras.get('dind'):
            try:
                host_docker_gid = grp.getgrnam('docker').gr_gid
                groups.append(host_docker_gid)
            except KeyError:
                warning('Could not find host group "docker"')

        volumes = config.get('bind_volumes', {})
        for vol in list(volumes):
            if user_home and '$HOME' in vol:
                host = vol.replace('$HOME', user_home)
                volumes[host] = volumes.pop(vol)

        for vol in extras.get('volumes', []):
            host, bind, mode = unpack_volume(vol)
            volumes[host] = {'bind': bind, 'mode': mode}

        # Maybe wrap and catch .close()
        bindfs = None
        if vault := self._vault(name):
            bindfs = TempFS()
            fs_root = bindfs.getsyspath("/")
            for secret in vault:
                sname = str(uuid.uuid4())
                spath = os.path.join(fs_root, sname)
                with open(spath, 'wb+') as f:
                    f.write(b64d(secret['file']))
                volumes[spath] = {'bind': secret['location'], 'mode': 'rw'}

        # As container network is in host mode, will exploit Xorg
        # abstract socket instead of /tmp/.X11-unix socket
        if config.get('forward_x11'):
            env.append('DISPLAY=%s' % os.environ.get('DISPLAY'))
            # Is run as root, probably not in xhost auth list
            if user_uid == 0:
                subprocess.call(
                    args=f'xhost +local:{ hostname }',
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT
                )

        self.image_manager.run(
            name='kitt',
            tag=name,
            hostname=hostname,
            volumes=volumes,
            environment=env,
            cap_add=['CAP_NET_RAW', 'CAP_IPC_LOCK'],
            extra_hosts={hostname: '127.0.0.1'},
            command=config.get('command', 'bash'),
            group_add=groups,
            user=f'{ user_uid }:{ user_gid }',
        )

        try:
            bindfs.close()
        except AttributeError:
            pass
        except TempFSErrors.OperationFailed:
            warning('Could not properly remove local tempfs.')
            warning('Sensible data might remain on disk.')

    def build(self, name: str, config_file: str):
        """Build kitt image using provided config file

        Args:
            name (str): kitt image name
            config_file (str): config file path
            catalog (str): custom catalog file
        """
        config = ConfigUtils.load(config_file)
        workspace = config.get('workspace')
        options = config.get('options')

        context = {
            'user': workspace.get('user', 'user'),
            'shell': workspace.get('default_shell', 'bash'),
            'tools': workspace.get('tools', []),
            'envs': workspace.get('envs', []),
            # !! Legacy code, needs better plugin generation
            'plugins': ['\n'.join(plugins.compose(n, c)) for n, c in config.get('plugins', {}).items()],
        }

        template = self.image_composer.compose(context)
        volumes = {}

        if options.get('docker_in_docker'):
            sock = '/var/run/docker.sock'
            volumes[sock] = {'bind': sock, 'mode': 'rw'}

        for vol in workspace.get('volumes', []):
            host = vol.get('host')
            bind = vol.get('bind')
            mode = vol.get('mode', 'rw')

            if not host or not bind:
                warning(f'Bad volume format : "{vol}"')
                continue

            volumes[host] = {'bind': bind, 'mode': mode}

        bind_config = {
            'entrypoint':    "fixuid -q",
            'bind_volumes':  volumes,
            'forward_x11':   options.get('forward_x11'),
            'dind':          options.get('docker_in_docker'),
            'hostname':      workspace.get('hostname'),
            'command':       workspace.get('default_shell'),
            'user':          workspace.get('user'),
            'version':       'v' + __version__,
        }

        with waiter('Building image'):
            labels = {'kitt-config': json.dumps(bind_config)}
            self.image_manager.build(
                'kitt', template, name, labels=labels, pull=True)

        success('Build success !')

    def list(self):
        """List local kitt images
        """
        self.image_manager.list(repository='kitt')

    def remove(self, name: str):
        """Remove local kitt image

        Args:
            name (str): image name
        """
        self.image_manager.remove('kitt', name)
        success('Done !')

    def prune(self):
        """Prune force all kitt images
        """
        self.image_manager.prune('kitt')

    def refresh(self):
        """Pull latest version of local kitt images
        """
        self.image_manager.refresh('kitt')

    def pull(self, repository: str, tag: str):
        """Pull remote kitt image from repository

        Args:
            repository (str): full repository url
            tag (str): remote image tag
        """

        if tag == 'latest':
            warning('Tag "latest" is deprecated.')
            warning('Use kitt image descriptor instead (Ex. "devops").')

        with waiter(f'Pulling image { tag } from registry'):
            self.image_manager.pull(repository, tag, 'kitt')

        labels = self.image_manager.labels('kitt', tag)
        if 'kitt-config' not in labels:
            warning('Image does not look like a kitt image')

        success('Pull done !')

    def push(self, repository: str, name: str):
        """Push local kitt image to remote repository

        Args:
            repository (str): full repository url
            name (str): local image name
        """
        if not self.image_manager.stat('kitt', name):
            panic(f'Image { name } not found')

        with waiter(f'Pushing image { name }'):
            self.image_manager.push(repository, 'kitt', name)

        success('Push done !')

    def inspect(self, name: str):
        """Show image runtime configuration metadata

        Args:
            name (str): image name
        """
        if not (config := self._config(name)):
            panic('Could not load image config metadata')

        config = json.dumps(config, indent=4)

        info(config)

    def patch(self, name: str):
        """Quick patch runtime kitt configuration (avoid rebuild)

        Args:
            name (str): image name
        """
        if not (config := self._config(name)):
            panic('Could not load image config metadata')

        config = json.dumps(config, indent=4)

        fd, fname = tempfile.mkstemp()
        with open(fd, 'w', encoding='utf-8') as tmpfile:
            tmpfile.write(config)

        editor = os.environ.get('EDITOR', 'vi')
        subprocess.call(
            args=f'{ editor } { fname }',
            shell=True
        )

        with open(fname, 'r', encoding='utf-8') as tmpfile:
            config = json.dumps(json.load(tmpfile))

        # !! Make sure kitt-vault is preserved
        # !! Image dockerfile better generation
        with waiter(f'Building patched image "{ name }-patch"'):
            self.image_manager.build(
                'kitt', f'FROM kitt:{ name }', f'{ name }-patch', labels={'kitt-config': config})

        os.unlink(fname)
        success('Patch success !')

    def _config(self, name: str) -> dict:
        """Kitt image config metadata

        Args:
            name (str): kitt image

        Returns:
            dict: JSON loaded config
        """

        labels = self.image_manager.labels('kitt', name)
        if 'kitt-config' not in labels:
            return None

        labels = labels.get('kitt-config')

        try:
            return json.loads(labels)
        except json.decoder.JSONDecodeError:
            return None

    def _vault(self, name: str) -> list:
        """Kitt image vault

        Args:
            name (str): kitt image

        Returns:
            dict: JSON loaded config
        """

        labels = self.image_manager.labels('kitt', name)
        if 'kitt-vault' not in labels:
            return None

        vault = labels.get('kitt-vault')
        info('Opening Kitt Vault')
        password = secure_prompt()

        if not (vault := uncipher_vault(password, vault)):
            warning('Invalid password or corrupted vault')

        return vault

# Where should I put you ??
def unpack_volume(volume: str) -> Tuple[str, str, str]:
    """Unpack docker like volume request to exploitable configuration tuple.

    Args:
        volume (str): docker like volume

    Returns:
        Tuple[str, str, str]: host, bind, mode
    """

    chunks = volume.split(':')
    nchunks = len(chunks)
    if not 1 < nchunks < 4:
        panic('Invalid --volume flag format')

    if nchunks == 2:
        host, bind = chunks
        return host, bind, 'ro'

    host, bind, mode = chunks
    if mode not in ['ro', 'rw']:
        panic(f'Unknown mode "{ mode }"')

    return host, bind, mode


client = KittClient()