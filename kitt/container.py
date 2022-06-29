import os
import io
import toml
import json
import time
import subprocess
import atexit

# Using docker lib for both docker and podman
# as API have similar bindings
import docker
import dockerpty

from . import plugins
from .logger import *

PATH =  os.path.dirname(__file__)

# Config utils
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

# Container Image abstraction
class ImageBuilder:
    def __init__(self, config, driver):
        try:
            with open( f'{PATH}/static/Dockerfile.{driver}', 'r') as df:
                self.template = df.read()

        except Exception as e:
            debug(e)
            panic('could not open proper Dockerfile for driver ' + drive)

        self.config = config

    def compose(self):
        dockerfile = self.template
        workspace = self.config['workspace']

        # store token => value to replace in template dockerfile
        composer = {}

        # Username inside container
        composer['user'] = workspace.get('user', 'user')

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

# I made the choice to support Podman for a few reasons.
# One of them is that Podman has an almost perfect compatibility support
# with docker environment. Podman even expose Docker's API endpoints
# an translate them to its own API enpoints.
# So we can use `docker-py` lib on podman socket with almost no additional cost
# and enjoy Podman's benefits (ligntness, native rootless containers..). 
# I could not find anyone else doing that, but for me it works like a charm.
class ContainerManager:
    def __init__(self, driver: str = None):
        local = self.get_local_config()
        self.driver = driver or local.get('driver') or 'docker'
        
        try:
            if self.driver == 'podman':
                self.client = self._from_podman()
            elif self.driver == 'docker':
                self.client = self._from_docker()
            else:
                raise NotImplementedError()

        except NotImplementedError:
            panic('Driver type does not exist')

        except docker.errors.APIError:
            panic('Could not connect to container socket')

        except docker.errors.DockerException as e:
            debug(e)
            panic('Problem trying to run container daemon')

    # _from_podman() is slightly slower than _from_docker()
    # as it needs to start podman api service.
    def _from_podman(self) -> docker.DockerClient:
        socket_url = 'unix:///tmp/podman-%s.sock' % os.getuid()
        socket_timeout = 5 # socket timeout in sec

        try:
            daemon = subprocess.Popen(["podman","system","service", "--time=0", socket_url])
        except FileNotFoundError:
            panic('Podman is not installed.\nIf you want to use Docker instead, run `kitt config --driver docker`.')
        
        atexit.register(daemon.terminate)

        for _ in range(socket_timeout * 5):
            try:
                client = docker.DockerClient(base_url = socket_url)
                return client
            except: time.sleep(0.2)

        raise docker.errors.APIError()

    def _from_docker(self) -> docker.DockerClient:
        return docker.from_env()

    # Start container
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
            stdin_open   = True,
            tty          = True,
            network_mode = 'host',
            volumes      = volumes,
            detach       = False,
            cap_add      = [ 'CAP_NET_RAW' ],
            environment  = env,
            user         = labels.get('user', 'root'),
            command      = labels.get('command', 'bash')
        )

        # Patch dockerpty to make it work with podman (see function doc bellow)
        if self.driver == 'podman':
            dockerpty.RunOperation._container_info = self._container_info
        
        dockerpty.start(self.client.api, container.id)
        

    # Ok let's explain a few things here.
    # This is a monkey patch function to abuse dockerpty.
    # Podman API does not handle AttachStdin/out/err, or at least it
    # drops it at container creation time. So dockerpty is broken as
    # it does check those parameters to decide either it's gonna attach
    # sockets or not. So we have to mock a fake config on our podman container
    # to force it to attach sockets on it.
    @staticmethod
    def _container_info(itself):
        monkey_config = {
            "Config": {
                "AttachStdin": True,
                "AttachStdout": True,
                # "AttachStderr": True, # TODO: Fix this
                "AttachStderr": False,  # > For some reason I have double stdout and no stderr
                "Tty": True,
                "OpenStdin": True,
                "StdinOnce": True,
            }
        }
        infos = itself.client.inspect_container(itself.container)
        infos.update(monkey_config)
        return infos

    # Build kitt image
    def build(self, name, config_file, catalog):
        if catalog:
            warning('Catalog custom input files not yet implemented, wille ignore.')

        config      = Config.load(config_file)
        # print(json.dumps(config, indent=4))
        # exit(0)
        dockerfile  = ImageBuilder(config, self.driver).compose()
        fileobj     = io.BytesIO(dockerfile.encode('utf-8'))
        volumes     = self.volumes(config)
        # print(dockerfile)
        # exit(0)

        user = "root"
        if self.driver == "podman":
            user = "1000:1000"

        with waiter(f'Building image'):
            try:
                self.client.images.build(
                    tag = 'kitt:%s' % name,
                    fileobj = fileobj,
                    pull = True,
                    nocache = True,
                    labels  = {
                        'kitt' : 'v0.1.0',
                        'hostname' : config['workspace']['hostname'],
                        'bind_volumes' : json.dumps(volumes),
                        'forward_x11' : str(config['options']['forward_x11']),
                        'user' : user,
                        'command' : config.get('default_shell', 'bash')
                    }
                )
            
            except docker.errors.APIError as e:
                debug(e)
                panic('Could not build image')

            except Exception as e:
                debug(e)

    # Pull image
    def pull(self, name: str):
        try:
            with waiter(f'Pulling image { name } from registry'):
                self.client.images.pull( name )
        
        except docker.errors.APIError:
            panic(f'Could not pull image { name }')
        
        except Exception as e:
            debug(e)
       
        success(f'Image { name } pull done')

    # Remove local image
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

    # Update all local images
    def refresh(self):
        [ img.reload() for img in self.images() ]

    # Check if local image is present
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
            images = self.client.images.list( filters = {'label' : 'kitt'} )

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

    # Generate local kitt config
    def set_local_config(self, driver: str):
        configmap = {}
        configmap['driver'] = driver
        
        if not (home := os.environ.get('HOME')):
            panic('Could not determine $HOME from env vars')

        home = os.path.join(home, '.kitt')

        if not os.path.exists(home):
            os.mkdir(home)

        with open(os.path.join(home, 'config.json'), 'w+') as f:
            json.dump(configmap, f, indent = 4)

    # Fetch local kitt config
    def get_local_config(self) -> dict:
        if not (home := os.environ.get('HOME')):
            return {}
        
        config_file = os.path.join(home, '.kitt/config.json')
        if not os.path.exists(config_file):
            return {}

        with open(config_file, 'r') as f:
            return json.load(f)

client = ContainerManager()