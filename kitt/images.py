"""Provides low-level container image abstractions"""

import io

from abc import ABC as AbstractClass, abstractmethod

import jinja2
import docker
import dockerpty


class Composer:
    """Image text file composer"""

    def __init__(self, template: str):
        """Init

        Args:
            template (str): jinja2 template
        """

        with open(template, 'r', encoding='utf-8') as file:
            self.template = file.read()

    def compose(self, values: dict) -> str:
        """Copose file from template

        Args:
            values (dict): templating values

        Returns:
            str: generated templated text file
        """

        template = jinja2.Template(self.template)
        return template.render(values)


class ImageManager(AbstractClass):
    """Abstract ImageManager

    Should be implemented by any image manager (docker, podman, ..)
    """

    @abstractmethod
    def run(self, name: str, tag: str = 'latest', **kwargs):
        """Create container, run and attach to current TTY.

        Args:
            name (str): image to run.
            tag (str, optional): image tag. Defaults to 'latest'.
            **kwargs (Any): any argument that undelying run method would accept.
        """
        raise NotImplementedError

    @abstractmethod
    def list(self, repository: str = None):
        """List local images

        Args:
            repository (str, optional): only for this repository. Defaults to None.
        """
        raise NotImplementedError

    @abstractmethod
    def remove(self, name: str, tag: str = 'latest'):
        """Remove local image

        Args:
            name (str): image name.
            tag (str, optional): image tag. Defaults to 'latest'.
        """
        raise NotImplementedError

    @abstractmethod
    def prune(self, repository: str = None):
        """Prune local images

        Args:
            repository (str, optional): only for this repository. Defaults to None.
        """
        raise NotImplementedError

    @abstractmethod
    def refresh(self, repository: str = None):
        """Pull latest version of local images

        Args:
            repository (str, optional): only for this repository. Defaults to None.
        """
        raise NotImplementedError

    @abstractmethod
    def build(self, name: str, template: str, tag: str = 'latest', **kwargs):
        """Build image

        Args:
            name (str): image name.
            template (str): text object to build image from (ex. Dockerfile).
            tag (str, optional): image tag. Defaults to 'latest'.
            **kwargs (Any): any argument that undelying build method would accept.
        """
        raise NotImplementedError

    @abstractmethod
    def pull(self, repository: str, tag: str = 'latest'):
        """Pull image from registry

        Args:
            repository (str): full repository url.
            tag (str, optional): image tag. Defaults to 'latest'.
            alias (str, optional): image name repository alias. Defaults to 'latest'.
        """
        raise NotImplementedError

    @abstractmethod
    def push(self, repository: str, name: str, tag: str = 'latest', clean: bool = True):
        """Push image to remote registry

        Args:
            repository (str): full repository url.
            name (str): local image name to push.
            tag (str, optional): image tag. Defaults to 'latest'.
            clean (bool, optional): Remove generated local tag. Defaults to True.
        """
        raise NotImplementedError

    @abstractmethod
    def stat(self, name: str, tag: str = 'latest'):
        """Stat if local image exists

        Args:
            name (str): image name.
            tag (str, optional): image tag. Defaults to 'latest'.
        """
        raise NotImplementedError

    @abstractmethod
    def labels(self, name: str, tag: str = 'latest') -> dict:
        """Get local image labels

        Args:
            name (str): image name.
            tag (str, optional): image tag. Defaults to 'latest'.

        Returns:
            dict: labels as dictionary.
        """
        raise NotImplementedError


def docker_error_handler(func):
    """Docker Error Generic Handler

    Args:
        func (types.FunctionType): _description_
    """

    def _handler(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except docker.errors.BuildError as error:
            self.logger.debug(error)
            self.logger.panic('Docker build error')
        except docker.errors.ImageNotFound as error:
            self.logger.debug(error)
            self.logger.panic('Local docker image not found')
        except docker.errors.APIError as error:
            self.logger.debug(error)
            self.logger.panic('Docker API error')
        except docker.errors.DockerException as error:
            self.logger.debug(error)
            self.logger.panic('Problem with docker daemon (--debug)')

    return _handler

# ---------------+
#     Docker     |
# ---------------+


class DockerImageManager(ImageManager):
    """Docker image manager (child class of ImageManager)"""

    @staticmethod
    def _tag(name, tag):
        return f'{ name }:{ tag }'

    @docker_error_handler
    def __init__(self, logger):
        self.logger = logger
        self.client = docker.from_env()
        self.experimental = self.client.info().get('ExperimentalBuild', False)

    @docker_error_handler
    def _get(self, name: str, tag: str = 'latest'):
        fname = self._tag(name, tag)
        return self.client.images.get(fname)

    @docker_error_handler
    def _get_all(self, repository: str = None) -> [docker.models.images.Image]:
        return self.client.images.list(name=repository)

    @docker_error_handler
    def run(self, name: str, tag: str = 'latest', **kwargs):
        fname = self._tag(name, tag)
        container = self.client.containers.create(
            image=fname,
            auto_remove=True,
            stdin_open=True,
            tty=True,
            detach=False,
            network_mode='host',
            **kwargs
        )
        dockerpty.start(self.client.api, container.id)

    @docker_error_handler
    def list(self, repository: str = None):
        images = self._get_all(repository)
        for image in images:
            basename = [x[len(repository) + 1:]
                        for x in image.tags if x.startswith(repository)].pop()
            self.logger.info('➜ ' + basename)

    @docker_error_handler
    def remove(self, name: str, tag: str = 'latest'):
        self.client.images.remove(self._tag(name, tag))

    @docker_error_handler
    def prune(self, repository: str = None):
        self.client.images.prune()
        if not repository:
            return
        for image in self._get_all(repository):
            for tag in image.tags:
                if tag.startswith(repository):
                    self.remove(*tag.split(':'))

    @docker_error_handler
    def refresh(self, repository: str = None):
        images = self._get_all(repository)
        map(lambda x: x.reload(), images)

    @docker_error_handler
    def build(self, name: str, template: str, tag: str = 'latest', squash = True, **kwargs):
        dockerfile = io.BytesIO(template.encode('utf-8'))
        fname = self._tag(name, tag)
        self.client.images.build(
            tag=fname,
            fileobj=dockerfile,
            rm=True,
            nocache=True,
            squash=squash and self.experimental,
            **kwargs
        )

    @docker_error_handler
    def pull(self, repository: str, tag: str = 'latest', alias: str = None):
        uri = f'{ repository }:{ tag }'
        if not (image := self.client.images.pull(uri)):
            self.logger.panic(f'Nothing to pull at { uri }')
        if alias and isinstance(alias, str):
            image.tag(alias, tag)

    @docker_error_handler
    def push(self, repository: str, name: str, tag: str = 'latest', clean: bool = True):
        self.logger.warning('Push status is not perfectly handled yet.')
        self.logger.warning('To see full push trace, run with --debug option.')

        image = self._get(name, tag)
        image.tag(repository, tag)
        output = self.client.images.push(repository, tag)
        self.logger.debug(output)
        if clean:
            self.remove(repository, tag)

    @docker_error_handler
    def stat(self, name: str, tag: str = 'latest') -> bool:
        return self._get(name, tag)

    @docker_error_handler
    def labels(self, name: str, tag: str = 'latest') -> dict:
        image = self._get(name, tag)
        return image.labels if image else {}
