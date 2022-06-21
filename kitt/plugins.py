from .logger import panic
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

        return cmdset

    # Should be implemented for each inherited Class of KittPlugin
    # Must return a list of lines in dockerfile format.
    @abstractmethod
    def _generate(self) -> [str]:
        pass

class BashPlugin(KittPlugin):
    def _generate(self) -> str:
        cmd = 'RUN echo "# Kitt Customs" >> /root/.bashrc'

        for extra in self.config.get('extras', []):
            cmd += ' && echo "%s" >> /root/.bashrc' % extra
        
        for alias in self.config.get('alias', []):
            name, cmd = alias['name'], alias['cmd']
            cmd += ' && echo alias %s="%s" >> /root/.bashrc' % (name, cmd)

        return [ cmd ]

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

        for plugin in self.config.get('plugins', []):
            cmd += ' -p "%s"' % plugin

        for extra in self.config.get('extras', []):
            cmd += ' -a "%s"' % extra

        for alias in self.config.get('alias', []):
            cmd += ' -a \'alias %s="%s"\'' % (alias['name'], alias['cmd'])

        cmdset.append(cmd)
        cmdset.append('ENTRYPOINT [ "/bin/zsh" ]')

        return cmdset

class TmuxPlugin(KittPlugin):
    def _generate(self) -> str:
        cmd = 'RUN catalog -v tmux'

        for extra in self.config.get('config', []):
            cmd += ' && echo "%s" >> /root/.tmux.conf' % extra

        return [ cmd ]

class ScreenPlugin(KittPlugin):
    def _generate(self) -> str:
        cmd = 'RUN catalog -v screen'

        for extra in self.config.get('config', []):
            cmd += ' && echo "%s" >> /root/.screenrc' % extra

        return [ cmd ]

class CopyPlugin(KittPlugin):
    def _generate(self) -> str:
        cmdset = []

        for file in self.config.get('files', []):
            src, dest = file['src'], file['dest']
            cmdset.append('COPY %s %s' % (src, dest))

        return cmdset

class DownloadPlugin(KittPlugin):
    def _generate(self) -> str:
        cmdset = []

        for res in self.config.get('ressources', []):
            url, target = res['url'], res['target']
            cmd = 'RUN wget -O %s %s --no-check-certificate' %s (target, url)
            cmdset.append(cmd)

        return cmdset

class GitPlugin(KittPlugin):
    def _generate(self) -> str:
        cmdset = []

        for repo in self.config.get('repos', []):
            url, target = repo['url'], repo['target']
            cmd = 'RUN git clone %s %s' %s (url, target)
            cmdset.append(cmd)

        return cmdset

plugins = {
    'bash'   : BashPlugin,
    'zsh'    : ZshPlugin,
    'tmux'   : TmuxPlugin,
    'screen' : ScreenPlugin,
    'copy'   : CopyPlugin,
    'git'    : GitPlugin,
    'download' : DownloadPlugin,
}

def compose(name: str, conf: dict) -> str:
    plugin = plugins.get(name)
    if plugin is None:
        panic('Unknown plugin "%s"' % name)

    return plugin(conf).generate()