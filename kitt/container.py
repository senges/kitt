import os
import io
import toml
import json
import time
import subprocess
import atexit

import docker
import dockerpty

from . import plugins
from .logger import *

PATH =  os.path.dirname(__file__)

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
            with open( template , 'r' ) as df:
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
    def __init__(self):
        try:
            self.client = docker.from_env()
        except docker.errors.APIError:
            panic('Could not connect to container socket')
        except docker.errors.DockerException as e:
            debug(e)
            panic('Problem trying to run container daemon')

    def run(self, name: str):
        name = 'kitt:%s' % name
        if not self.stat(name):
            panic(f'Image { name } not found locally. Use `pull` command or add `--pull` flag.')

        img = self.client.images.get(name)
        labels = img.labels
        if not labels.get('kitt'):
            warning('%s is not a kitt image, might not work properly.' % name)

        hostname = labels.get('hostname', 'kitt')
        volumes = labels.get('bind_volumes', '{}')
        volumes = json.loads(volumes)
        env = []

        # Setup X11 forwarding
        # As container network is in host mode, will exploit Xorg
        # abstract socket instead of /tmp/.X11-unix socket
        if labels.get('forward_x11'):
            env.append( 'DISPLAY=%s' % os.environ.get('DISPLAY') )
            # Is run as root, probably not in xhost auth list
            if os.getuid() == 0:
                subprocess.call(
                    args   = [ 'xhost', '+local:%s' % hostname ],
                    stdout = subprocess.DEVNULL,
                    stderr = subprocess.STDOUT
                )

        container = self.client.containers.create(
            image        = name,
            auto_remove  = True,
            hostname     = hostname,
            extra_hosts  = { hostname : "127.0.0.1" },
            stdin_open   = True,
            tty          = True,
            network_mode = 'host',
            volumes      = volumes,
            detach       = False,
            cap_add      = [ 'CAP_NET_RAW' ],
            environment  = env,
            user         = labels.get('user', 'root'),
            command      = labels.get('command', 'bash'),
        )
        
        dockerpty.start(self.client.api, container.id)

    def build(self, name, config_file, catalog):
        if catalog:
            warning('Catalog custom input files not yet implemented, wille ignore.')

        config      = Config.load(config_file)
        # print(json.dumps(config, indent=4))
        # exit(0)
        dockerfile  = ImageBuilder(config).compose()
        fileobj     = io.BytesIO(dockerfile.encode('utf-8'))
        volumes     = self.volumes(config)
        # print(dockerfile)
        # exit(0)

        with waiter(f'Building image'):
            try:
                self.client.images.build(
                    tag = 'kitt:%s' % name,
                    fileobj = fileobj,
                    pull = True,
                    nocache = True,
                    labels  = {
                        'kitt':          'v0.2.1',
                        'hostname':      config['workspace']['hostname'],
                        'bind_volumes':  json.dumps(volumes),
                        'forward_x11':   str(config['options']['forward_x11']),
                        'command':       config.get('default_shell', 'bash'),
                        'user':          "1000:1000",
                        'entrypoint':    "fixuid -q",
                    }
                )
            
            except docker.errors.APIError as e:
                debug(e)
                panic('Could not build image')

            except Exception as e: debug(e)

    def pull(self, name: str):
        with waiter(f'Pulling image { name } from registry'):
            try: self.client.images.pull( name )

            except docker.errors.APIError:
                panic(f'Could not pull image { name }')

            except Exception as e: debug(e)
       
        success(f'Image { name } pull done')

    def push(self, name: str, repository: str):
        panic("Push strategy not yet implemented")

    def remove(self, name: str):
        image = 'kitt:%s' % name

        if not self.stat(image):
            panic('Local image "%s" does not exist' % name)
        try:
            self.client.images.remove(image = image)
        except Exception as e:
            debug(e)
            panic('Could not remove local image "%s"' % name)

        success('Done !')

    def refresh(self):
        [ img.reload() for img in self.images() ]

    def stat(self, name: str) -> docker.models.images.Image:
        try:
            img = self.client.images.get(name)

        except docker.errors.ImageNotFound:
            return None
        
        except Exception as e:
            debug(e)

        return img

    # List kitt labeled images
    def images(self) -> [docker.models.images.Image]:
        try:
            images = self.client.images.list( name = "kitt" )

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
            volset[sock] = { 'bind' : sock, 'mode' : 'rw' }

        # Share home folder (read-write)
        if config['options']['bind_home_folder']:
            home = os.environ.get('HOME')
            volset[home] = { 'bind' : '/root', 'mode' : 'rw'}

        # Share ssh folder (read-only)
        # Will shadow $HOME/.ssh bind if set above
        if config['options']['bind_ssh_folder']:
            ssh = '%s/.ssh' % os.environ.get('HOME')
            volset[ssh] = { 'bind' : '/root/.ssh', 'mode' : 'ro' }

        # Add custom volumes
        for vol in config['workspace'].get('volumes', []):
            host = vol.get('host')
            bind = vol.get('bind')
            mode = vol.get('mode', 'rw')

            if not host or not bind:
                warning('Bad volume format : "%s"' % vol)
                continue

            volset[host] = { 'bind' : bind, 'mode' : mode }

        return volset

client = ContainerManager()