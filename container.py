import io
import toml
import docker
import dockerpty

import plugins
from logger import *

class Config:

    @staticmethod
    def load(config_file: str = None):
        try:
            default = toml.load('static/default.toml')

            if config_file:
                custom = toml.load(config_file)
                default.update(custom)

        except FileNotFoundError as e:
            panic('could not open file ' + e.filename)

        except Exception as e:
            debug(e)
            panic('Error loading config files')

        # Handle incomplete user config file
        return default

# Docker image abstraction
class ImageBuilder:
    def __init__(self, config):
        try:
            with open('static/Dockerfile.template', 'r') as df:
                self.template = df.read()
                
        except Exception as e:
            debug(e)
            panic('could not open Dockerfile.template')

        self.config = config

    def compose(self):
        dockerfile = self.template

        # store token => value to replace in template dockerfile
        composer = {}

        # Tools to install with Catalog
        composer['tools'] = self.config['workspace']['tools']

        # Plugins to append in Dockerfile
        composer['plugins'] = []

        for name, config in self.config['plugins'].items():
            extra = plugins.compose(name, config)
            composer['plugins'].append(extra)

        # Replace key by line block in template
        for key, value in composer.items():
            lineset = ' '.join(value)
            template = template.replace('__%s__' % key, lineset)

        return dockerfile

# Docker wrapper
class DockerWrapper:
    def __init__(self):
        try:
            self.client = docker.from_env()

        except docker.errors.APIError:
            panic('Could not connect to docker socket')

        except docker.errors.DockerException as e:
            debug(e)
            panic('Problem trying to run docker')

    # Start container
    def run(self, name: str, volumes: dict = {}, env: list = []):
        if not self.stat(name):
            panic(f'Image { name } not found locally. Use `pull` command or add `--pull` flag.')

        container = self.client.containers.create(
            image        = name,
            auto_remove  = True,
            hostname     = 'kitt',
            stdin_open   = True,
            tty          = True,
            network_mode = 'host',
            volumes      = volumes,
            environment  = env,
        )

        dockerpty.start(self.client.api, container.id)

    # Pull docker image
    def pull(self, name: str):

        try:
            with waiter(f'Pulling image { name } from registry'):
                self.client.images.pull( name )
        
        except docker.errors.APIError:
            panic(f'Could not pull image { name }')
        
        except Exception as e:
            debug(e)
       
        success(f'Image { name } pull done')

    # Update all local images
    def refresh(self):
        pass

    # Check if local image is present
    def stat(self, name: str):
        try:
            img = self.client.images.get(name)

        except docker.errors.ImageNotFound:
            return None
        
        except Exception as e:
            debug(e)

        return img

    # Docker volume list generation
    def volumes(self):
        pass

    # Build kitt image
    def build(self, config_file, catalog):

        if catalog:
            warning('Catalog custom input files not yet implemented, wille ignore.')

        config      = Config.load(config_file)
        dockerfile  = ImageBuilder(config).compose()
        fileobj     = io.BytesIO(dockerfile.encode('utf-8'))

        try:
            with waiter(f'Building image'):
                self.client.images.build(
                    fileobj = fileobj,
                    nocache = True,
                    tag     = 'kittd',
                    labels  = {
                        'kitt' : 'v0.1',
                        'hostname' : config['workspace']['hostname']
                    }
                )
        
        except docker.errors.APIError as e:
            debug(e)
            panic('Could not build image')

        except Exception as e:
            debug(e)

    def images(self):
        try:
            images = self.client.images.list( filters = {'label' : 'kitt'} )

        except docker.errors.APIError as e:
            debug(e)
            panic('Could not list local images')

        except Exception as e:
            debug(e)

        return images

client = DockerWrapper()