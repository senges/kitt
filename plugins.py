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
            "zstyle ':completion:*:commands' rehash 1",
            "export SHELL=/usr/bin/zsh",
            "export EDITOR=$(which vi)"
        ]

        self.config['alias'].append({
            'name': 'tools',
            'cmd': 'catalog --list'
        })

        for plugin in self.config['plugins']:
            cmd += ' -p "%s"' % plugin

        for extra in self.config['extras']:
            cmd += ' -a "%s"' % extra

        for alias in self.config['alias']:
            cmd += ' -a \'alias %s="%s"\'' % (alias['name'], alias['cmd'])

        cmdset.append(cmd)
        cmdset.append('ENTRYPOINT [ "/bin/zsh" ]')

        return cmdset

class TmuxPlugin(KittPlugin):
    def _generate(self) -> str:
        cmd = 'RUN catalog -v tmux'

        for extra in self.config['extras']:
            cmd += ' && echo "%s" >> /root/.tmux.conf' % extra

        return [ cmd ]

class ScreenPlugin(KittPlugin):
    def _generate(self) -> str:
        cmd = 'RUN catalog -v screen'

        for extra in self.config['extras']:
            cmd += ' && echo "%s" >> /root/.screenrc' % extra

        return [ cmd ]

plugins = {
    'zsh'    : ZshPlugin,
    'tmux'   : TmuxPlugin,
    'screen' : ScreenPlugin
}

def compose(name: str, conf: dict) -> str:
    plugin = plugins.get(name)
    if plugin is None:
        panic('Unknown plugin "%s"' % name)

    return plugin(conf).generate()