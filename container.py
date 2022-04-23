import io
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
class ImageBuilder:
    def __init__(self, config: Config):
        try:
            with open('static/Dockerfile.template', 'r') as df:
                self.template = df.read()
        except:
            panic('could not open Dockerfile.template')

        self.config = config

    def compose(self):
        tools      = self.config.image.tools
        zsh_theme  = self.config.zsh.theme
        zsh_extras = []

        for plugin in self.config.zsh.plugins:
            zsh_extras.append( '-p "%s"' % plugin )

        for extra in self.config.zsh.extras:
            zsh_extras.append( '-a "%s"' % extra )

        return self.replace([
            ('ZSH-EXTRA', zsh_extras),
            ('ZSH-THEME', zsh_theme),
            ('TOOLS', tools)
        ])

    def replace(self, tup):
        template = self.template
        for k, v in tup:
            if isinstance(v, list):
                v = ' '.join(v)
            template = template.replace('{{%s}}' % k, v)

        return template

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
    def build(self, config_file: str):

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
                        'hostname' : config.image.hostname
                    }
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