import os
import io
import grp
import uuid
import toml
import json
import tempfile
import subprocess

import docker
import dockerpty


from importlib.metadata import version as pip_version
from fs.tempfs import TempFS
from typing import Union

from . __version__ import __version__

from . import plugins
from .crypto import b64d, uncipher_vault, secure_prompt
from .logger import *

PATH = os.path.dirname(__file__)


class Config:

    @staticmethod
    def load(config_file: str = None):
        try:
            custom = {}
            default = toml.load(PATH + '/static/default.toml')
            if config_file:
                custom = toml.load(config_file)

        except toml.TomlDecodeError:
            with open(config_file, 'r') as f:
                custom = json.load(f)

        except FileNotFoundError as e:
            panic('could not open file ' + e.filename)

        except Exception as e:
            debug(e)
            panic('Error loading config files')

        finally:
            # Handle incomplete user config file
            default = Config.update(custom, default)

        return default

    # Deep update dict config `src' with config `dest'
    # Make sure it wont overwrite if empty str or list.
    @staticmethod
    def update(src: dict, dest: dict):
        for k, v in src.items():
            if k in dest and isinstance(v, dict) and isinstance(dest[k], dict):
                dest[k] = Config.update(src[k], dest[k])
            elif k in dest and v in ['', [], ['']]:
                continue
            else:
                dest[k] = src[k]

        return dest


class ImageBuilder:
    def __init__(self, config):
        template = '%s/static/Dockerfile.template' % PATH
        try:
            with open(template, 'r') as df:
                self.template = df.read()

        except Exception as e:
            debug(e)
            panic('could not open ' + template)

        self.config = config

    def compose(self):
        dockerfile = self.template
        workspace = self.config['workspace']

        # store token => value to replace in template dockerfile
        composer = {}

        # Username inside container
        composer['user'] = workspace.get('user', 'user')
        composer['shell'] = workspace.get('default_shell', 'bash')

        # Tools to install with Catalog
        composer['tools'] = 'RUN catalog -v utils '
        composer['tools'] += ' '.join(workspace.get('tools', []))

        # Evironment variables
        # (Better at runtime ?)
        composer['envs'] = []
        for env in workspace.get('envs', []):
            line = 'ENV %s="%s"' % (env['name'], env['value'])
            composer['envs'].append(line)

        # Plugins to append in Dockerfile
        composer['plugins'] = []
        for name, config in self.config['plugins'].items():
            extra = plugins.compose(name, config)
            composer['plugins'] += extra
            composer['plugins'].append('')

        # Replace key by line block in template
        for key, value in composer.items():
            if isinstance(value, list):
                value = '\n'.join(value)
            dockerfile = dockerfile.replace('__%s__' % key, value)

        return dockerfile


class ContainerManager:

    def __init__(self):
        try:
            self.client = docker.from_env()
        except docker.errors.APIError:
            panic('Could not connect to container socket')
        except docker.errors.DockerException as e:
            debug(e)
            panic('Problem trying to run container daemon')

    def run(self, image: str, extras: dict = {}):
        env = []
        name = self._tag(image)

        if not (image := self.stat(name)):
            panic('Image %s not found. Use `pull` command first.' % name)

        # LABELS
        labels = self.get_image_labels(image)

        # HOSTNAME
        hostname = labels.get('hostname', 'kitt')
        
        # DOCKER IN DOCKER
        groups = []
        if  labels.get('dind', False):
            try:
                host_docker_gid = grp.getgrnam('docker').gr_gid
                groups.append(host_docker_gid)
            except: pass

        # VOLUMES
        volumes = labels.get('bind_volumes', {})
        home = os.environ.get('HOME')
        for vol in list(volumes):
            if home and '$HOME' in vol:
                host = vol.replace('$HOME', home)
                volumes[host] = volumes.pop(vol)

        for vol in extras.get('volumes', []):
            host, bind, mode = self.unpack_volume(vol)
            volumes[host] = {'bind': bind, 'mode': mode}

        # VAULT
        secrets = self.uncipher_vault(image)
        if secrets:
            fs = TempFS()
            fs_root = fs.getsyspath("/")
            for secret in secrets:
                sname = str(uuid.uuid4())
                spath = os.path.join(fs_root, sname)
                with open(spath, 'wb+') as f:
                    f.write(b64d(secret['file']))
                volumes[spath] = {'bind': secret['location'], 'mode': 'rw'}

        # Setup X11 forwarding
        # As container network is in host mode, will exploit Xorg
        # abstract socket instead of /tmp/.X11-unix socket
        if labels.get('forward_x11'):
            env.append('DISPLAY=%s' % os.environ.get('DISPLAY'))
            # Is run as root, probably not in xhost auth list
            if os.getuid() == 0:
                subprocess.call(
                    args=['xhost', '+local:%s' % hostname],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT
                )

        container = self.client.containers.create(
            image=image,
            hostname=hostname,
            volumes=volumes,
            environment=env,
            auto_remove=True,
            stdin_open=True,
            tty=True,
            detach=False,
            network_mode='host',
            cap_add=['CAP_NET_RAW', 'CAP_IPC_LOCK'],
            extra_hosts={hostname: "127.0.0.1"},
            user=labels.get('user', 'root'),
            command=labels.get('command', 'bash'),
            group_add = groups
        )

        dockerpty.start(self.client.api, container.id)
        
        try: fs.close()
        except: pass
        # self.client.containers.prune(filters={'label': 'kitt-config'})

    @staticmethod
    def _tag(x): return 'kitt:%s' % x

    @staticmethod
    def get_image_labels(image: docker.models.images.Image) -> dict:
        labels = image.labels.get('kitt-config', '')

        if not labels:
            panic('%s is not a kitt image.' % image)
        try:
            return json.loads(labels)
        except:
            panic("Invalid label format.")

    @staticmethod
    def uncipher_vault(image: docker.models.images.Image) -> list:
        vault = image.labels.get('kitt-vault', '')

        if not vault:
            return None
        try:
            info('Opening Kitt Vault')
            password = secure_prompt()
            return uncipher_vault(password, vault)
        except Exception as e:
            debug(e)
            warning("Invalid vault format.")
            return None

    def build(self, name, config_file, catalog):
        if catalog:
            warning('Catalog custom input files not yet implemented, wille ignore.')

        config = Config.load(config_file)
        dockerfile = ImageBuilder(config).compose()
        fileobj = io.BytesIO(dockerfile.encode('utf-8'))
        volumes = self.volumes(config)

        bind_config = {
            'entrypoint':    "fixuid -q",
            'bind_volumes':  volumes,
            'forward_x11':   config['options']['forward_x11'],
            'dind':          config['options']['docker_in_docker'],
            'hostname':      config['workspace']['hostname'],
            'command':       config['workspace']['default_shell'],
            'user':          config['workspace']['user'],
            'version':       'v' + __version__,
        }

        with waiter('Building image'):
            try:
                # catalog = self.stat('senges/catalog')
                # catalog.reload()
                self.client.images.build(
                    tag=self._tag(name),
                    fileobj=fileobj,
                    pull=True,
                    rm=True,
                    nocache=True,
                    labels={
                        'kitt-config': json.dumps(bind_config)
                    }
                )

            except docker.errors.APIError as e:
                debug(e)
                panic('Could not build image')

            except Exception as e:
                debug(e)

        success('Build success !')

    def pull(self, url: str, tag: str):
        if tag == 'latest':
            warning(
                'Tag `latest` is deprecated, use kitt image descriptor instead (Ex. `devops`)')

        full_image = '%s:%s' % (url, tag)
        with waiter(f'Pulling image { full_image } from registry'):
            try:
                image = self.client.images.pull(full_image)
                if not image.labels.get('kitt-config'):
                    warning('Image does not look like a kitt image')
                image.tag('kitt', tag)
            except docker.errors.APIError:
                panic(f'Could not pull image { url }')

            except Exception as e:
                debug(e)

        success(f'Image { tag } pull done')

    def push(self, repository: str, name: str):
        warning('Push status is not perfectly handled yet.')
        warning('To see full push trace, run with --debug option.')

        image = self.stat(self._tag(name))
        while repository.endswith('/'):
            repository = repository[:-1]
        if not image:
            panic('Image not found')
        try:
            image.tag(repository, name)
            with waiter(f'Pushing image'):
                output = self.client.images.push(repository, name)
            self.client.images.remove('%s:%s' % (repository, name))
            debug(output)
        except Exception as e:
            debug(e)
            panic('Something went wrong')

        success('Push done !')

    def remove(self, name: str):
        image = self._tag(name)

        if not self.stat(image):
            panic('Local image "%s" does not exist' % name)
        try:
            self.client.images.remove(image=image)
        except Exception as e:
            debug(e)
            panic('Could not remove local image "%s"' % name)

        success('Done !')

    def prune(self):
        for image in self.images():
            try:
                self.client.images.remove(image=image.tags[0])
            except Exception as e:
                debug(e)
                panic('Could not remove local image "%s"' % image.tags[0])

        self.client.images.prune()

    def inspect(self, name: str):
        tag = self._tag(name)

        if not (image := self.stat(tag)):
            panic('Image do not exist or is not a kitt image.')

        labels = image.labels.get('kitt-config', {})
        labels = json.dumps(json.loads(labels), indent=4)
        
        info(labels)

    def patch(self, name: str):
        tag = self._tag(name)

        if not (image := self.stat(tag)):
            panic('Image do not exist or is not a kitt image.')

        labels = image.labels.get('kitt-config', {})
        labels = json.dumps(json.loads(labels), indent=4)

        fd, fname = tempfile.mkstemp()
        with open(fname, 'w') as f:
            f.write(labels)

        editor = os.environ.get('EDITOR', 'vi')
        subprocess.call(
            editor + ' ' + fname,
            shell=True
        )

        with open(fname, 'r') as f:
            labels = json.dumps(json.load(f))

        dockerfile = 'FROM %s' % tag
        fileobj = io.BytesIO(dockerfile.encode('utf-8'))

        with waiter(f'Building patched image'):
            try:
                self.client.images.build(
                    tag=tag + '-patch',
                    fileobj=fileobj,
                    rm=True,
                    labels={'kitt-config': labels}
                )
            except docker.errors.APIError as e:
                debug(e)
                panic('Could not build image')
            except Exception as e:
                debug(e)

        success('Patch success "%s-patch" !' % tag)

        os.close(fd)
        os.unlink(fname)

    def refresh(self):
        [img.reload() for img in self.images()]

    def stat(self, name: str) -> docker.models.images.Image:
        try:
            return self.client.images.get(name)

        except docker.errors.ImageNotFound:
            return None

        except Exception as e:
            debug(e)

        return None

    # List kitt labeled images
    def images(self) -> [docker.models.images.Image]:
        try:
            images = self.client.images.list(name="kitt")

        except docker.errors.APIError as e:
            debug(e)
            panic('Could not list local images')

        except Exception as e:
            debug(e)

        return images

    @staticmethod
    def unpack_volume(volume: str) -> (str, str, str):
        chunks = volume.split(':')
        if not (1 < len(chunks) < 4):
            panic("Invalid --volume flag format")

        host = chunks[0]
        bind = chunks[1]
        try:
            mode = chunks[2]
        except:
            mode = "ro"

        return host, bind, mode

    # Volume list generation
    def volumes(self, config: dict) -> dict:
        volset = {}

        # Share docker socket
        if config['options']['docker_in_docker']:
            sock = '/var/run/docker.sock'
            volset[sock] = {'bind': sock, 'mode': 'rw'}

        # Add custom volumes
        for vol in config['workspace'].get('volumes', []):
            host = vol.get('host')
            bind = vol.get('bind')
            mode = vol.get('mode', 'rw')

            if not host or not bind:
                warning('Bad volume format : "%s"' % vol)
                continue

            volset[host] = {'bind': bind, 'mode': mode}

        return volset


client = ContainerManager()
