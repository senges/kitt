import io
import toml
import docker
import dockerpty

from logger import *

# Docker image abstraction
class ImageBuilder:
    def __init__(self, config):
        try:
            with open('static/Dockerfile.template', 'r') as df:
                self.template = df.read()
        except:
            panic('could not open Dockerfile.template')

        self.config = config

    def compose(self):
        raise NotImplementedError('Will switch to plugins next commit')

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

    # Build kitt image
    def build(self, config_file: str):

        config      = toml.load(config_file)
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
            print(e)
            panic('Could not build image')

    def images(self):
        try:
            images = self.client.images.list( filters = {'label' : 'kitt'} )

        except docker.errors.APIError :
            panic('Could not list local images')

        return images

client = DockerWrapper()