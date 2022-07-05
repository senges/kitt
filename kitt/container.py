import os
import io
import toml
import json
import subprocess

import docker
import dockerpty

from typing import Union

from . import plugins
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

    def _file(src: str, dest: str) -> [str]:
        pass

# Might still contains legacy code about Podman
# See branch feat/podman for podman integration wip


class ContainerManager:
    def _tag(_, x): return 'kitt:%s' % x

    def __init__(self):
        try:
            self.client = docker.from_env()
        except docker.errors.APIError:
            panic('Could not connect to container socket')
        except docker.errors.DockerException as e:
            debug(e)
            panic('Problem trying to run container daemon')

    def run(self, image: str):
        env = []
        name = self._tag(image)

        if not (image := self.stat(name)):
            panic(
                'Image %s not found locally. Use `pull` command or add `--pull` flag.' % image)

        # // LABELS // #
        labels = image.labels.get('kitt-config', '')

        if not labels:
            panic('%s is not a kitt image.' % image)

        try:
            labels = json.loads(labels)
        except:
            panic("Invalid label format.")

        # // HOSTNAME // #
        hostname = labels.get('hostname', 'kitt')

        # volumes = { "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"}}
        # // VOLUMES // #
        volumes = labels.get('bind_volumes', {})
        user = labels.get('user', 'user')
        home = os.environ.get('HOME', None)

        if not home:
            warning("$HOME is not exported, will skip any relative bind volume")

        # Share home folder (read-write)
        if home and config['options']['bind_home_folder']:
            volumes[home] = {'bind': '/home/%s/share' % user, 'mode': 'rw'}

        # Share ssh folder (read-only)
        # Will shadow $HOME/.ssh bind if set above
        if home and config['options']['bind_ssh_folder']:
            ssh = '%s/.ssh' % home
            volset[ssh] = {'bind': '/home/%s/.ssh' % user, 'mode': 'ro'}

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
            cap_add=['CAP_NET_RAW'],
            extra_hosts={hostname: "127.0.0.1"},
            user=labels.get('user', 'root'),
            command=labels.get('command', 'bash'),
        )

        dockerpty.start(self.client.api, container.id)

    def build(self, name, config_file, catalog):
        if catalog:
            warning('Catalog custom input files not yet implemented, wille ignore.')

        config = Config.load(config_file)
        dockerfile = ImageBuilder(config).compose()
        fileobj = io.BytesIO(dockerfile.encode('utf-8'))
        volumes = self.volumes(config)
        # print(dockerfile)
        # exit(0)

        bind_config = {
            'version':       'v0.2.1',
            'entrypoint':    "fixuid -q",
            'bind_volumes':  volumes,
            'hostname':      config['workspace']['hostname'],
            'bind_home':     config['options']['bind_home_folder'],
            'bind_ssh':      config['options']['bind_ssh_folder'],
            'forward_x11':   config['options']['forward_x11'],
            'command':       config['workspace']['default_shell'],
            'user':          config['workspace']['user'],
        }

        with waiter(f'Building image'):
            try:
                self.client.images.build(
                    tag=self._tag(name),
                    fileobj=fileobj,
                    pull=True,
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

        success("Build success !")

    def pull(self, name: str):
        with waiter(f'Pulling image { name } from registry'):
            try:
                self.client.images.pull(name)

            except docker.errors.APIError:
                panic(f'Could not pull image { name }')

            except Exception as e:
                debug(e)

        success(f'Image { name } pull done')

    def push(self, name: str, repository: str):
        panic("Push strategy not yet implemented")

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

    def patch(self, name: str):
        raise NotImplementedError()

        import tempfile
        tag = self._tag(name)

        if not (image := self.stat(tag)):
            panic("Image do not exist or is not a kitt image.")

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
            labels = json.load(f)

        # OK this doesn't work
        # Can't patch image like this
        image.labels['kitt-config'] = json.dumps(labels)
        image.tag(tag + '-patch')
        image.reload()

        # with waiter(f'Generating patch image'):
        # archive = '/tmp/kitt-export.tar'
        # with open(archive, 'wb') as f:
        # self.client.images.load(image.save(named = tag + '-patch'))
        # self.client.api.import_image_from_stream(image.save(), repository="kitt", tag=name + '-patch')
        # image.save()
        #     for chunk in image.save():
        #         f.write(chunk)

        # with open(archive, 'rb') as f:
        #     self.client.api.load_image(f.read())

        # self.client.api.import_image(src=archive, repository="kitt", tag=name + '-patch')

        # os.close(fd)
        # os.unlink(fname)
        # os.unlink(archive)

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
