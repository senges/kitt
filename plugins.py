from logger import panic
from abc import ABC as AbstractClass, abstractmethod

# Every plugin must inherit KittPlugin class and implement
# custom _generate() method which returns and array of
# Dockerfile commands.

class KittPlugin(AbstractClass):
    def __init__(self, config):
        self.config = config
        self.name = self.__class__.__name__

    def generate(self) -> [str]:
        cmdset = [ '# Plugin:' + self.name ]
        cmdset += self._generate()

        return '\n'.join(cmdset) + '\n'

    # Should be implemented for each inherited Class of KittPlugin
    # Must return a list of lines in dockerfile format.

    @abstractmethod
    def _generate(self) -> [str]:
        pass

class ZshPlugin(KittPlugin):
    def _generate(self) -> str:

        cmdset = [ 'RUN catalog -v zsh-in-docker' ]
        
        cmd = 'RUN zsh-in-docker'
        cmd += ' -t "%s"' % self.config['theme']
        
        # Few default additional config
        self.config['extras'] += [
            "alias tools='catalog --list'",
            "zstyle ':completion:*:commands' rehash 1",
            "export SHELL=/usr/bin/zsh",
            "export EDITOR=$(which vi)"
        ]

        for plugin in self.config['plugins']:
            cmd += ' -p "%s"' % plugin

        for extra in self.config['extras']:
            cmd += ' -a "%s"' % extra

        cmdset.append(cmd)
        cmdset.append('ENTRYPOINT [ "/bin/zsh" ]')

        return cmdset

plugins = {
    'zsh' : ZshPlugin,
}

def compose(name: str, conf: dict) -> str:
    plugin = plugins.get(name)
    if plugin is None:
        panic('Unknown plugin "%s"' % name)

    return plugin(conf).generate()