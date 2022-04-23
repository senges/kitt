from logger import panic
from abc import ABC as AbstractClass, abstractmethod

class KittPlugin(AbstractClass):
    def __init__(self, config):
        self.config = config
        pass

    @abstractmethod
    def generate(self) -> [str]:
        pass

class ZshPlugin(KittPlugin):
    def generate(self):

        cmdset = []
        cmdset.append('RUN catalog -v zsh-in-docker')
        
        cmd = 'RUN zsh-in-docker'
        cmd += ' -t %s' % self.config['theme']
        
        # Few default additional config
        self.config['extras'] += [
            "alias tools='catalog --list'",
            "zstyle ':completion:*:commands' rehash 1",
            "export SHELL=$(which zsh)",
            "export EDITOR=$(which vim)"
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