import toml
import json
import docker
import dockerpty

from types import SimpleNamespace
from logger import *

# Config file wrapper object
class Config(SimpleNamespace):

    # > Will handle default value in the future
    # > in order to accept incomplete config file from client
    def __getattribute__(self, value):
        try:
            return super().__getattribute__(value)

        except AttributeError:
            return None

    # > Will convert toml into json in order to abuse `object_hook' handler
    # > toml -> json -> Config(SimpleNamespace)
    @staticmethod
    def load(file: str):
        try:
            toml_config     = toml.load(file)
            json_config     = json.dumps(toml_config)
            config_object   = json.loads(
                json_config,
                object_hook = lambda x: Config(**x)
            )
        except:
            panic('Could not load config file')

        return config_object

# Docker image abstraction
class ImageWrapper:
    def __init__(slef):
        pass

# Docker wrapper
class DockerWrapper:
    def __init__(self):
        try:
            self.client = docker.from_env()

        except docker.errors.APIError:
            panic('Could not connect to docker socket')

        except docker.errors.DockerException:
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

        return img

    # Docker volume list generation
    def volumes(self):
        pass

    def env(self):
        pass

    def init(self):
        pass

    # Build kitt image
    def build(self):
        try:
            with waiter(f'Building image'):
                self.client.images.build(
                    path = 'static',
                    # nocache = True,
                    tag = 'kittd',
                    labels = { 'kitt' : '' }
                )
        
        except docker.errors.APIError as e:
            print(e)
            panic('Could not build image')

    def images(self):
        try:
            images = self.client.images.list( filters = {'label' : 'kitt'} )

        except docker.errors.APIError :
            panic('Could not list local images')

        return images

client = DockerWrapper()