import os
import uuid

from fs.tempfs import TempFS, errors as TempFSErrors

from kitt.crypto import b64, b64d, cipher_dict, secure_prompt, uncipher_dict
from kitt.logger import warning, info

class VaultFS:
    """Vault tmp filesystem to mount secrets
    """
    bindfs = None

    def __init__(self):
        self.bindfs = TempFS()
        self.fs_root = self.bindfs.getsyspath('/')

    def load(self, files: [str]) -> dict:
        """Load files in tmpfs

        Args:
            files [str]: base64 encoded files

        Returns:
            dict: file mapping list
        """

        volumes = {}

        for file in files:
            fname = str(uuid.uuid4())
            fpath = os.path.join(self.fs_root, fname)

            with open(fpath, 'wb+') as fout:
                fout.write(b64d(file['file']))

            volumes[fpath] = {
                'bind': file['location'],
                'mode': 'rw',
            }
            
        return volumes

    def close(self):
        """Close temp filesystem
        """
        try:
            self.bindfs.close()
        except AttributeError:
            pass
        except TempFSErrors.OperationFailed:
            warning('Could not properly remove local tempfs.')
            warning('Sensible data might remain on disk.')

def create_vault(config: dict) -> str:
    """Create base64 encoded encrypted vault to attach
    """

    info('Remember secret strengh is proportional to password strengh.')
    info('Most of the time, a strong password is a long password.')

    password = secure_prompt()

    vault = {
        'files': [],
        'envs': {},
    }

    for file in config.get('files', []):
        src, dest = file['src'], file['dest']
        with open(src, 'rb') as raw_file:
            raw = raw_file.read()
            raw = b64(raw)
        vault['files'].append({
            'location': dest,
            'file': raw
        })

    for env in config.get('envs', []):
        name, value = env['name'], env['value']
        vault['envs'][name] = value

    return cipher_dict(password, vault)

def load_vault(str_vault: str) -> dict:
    """Load base64 encoded encrypted vault
    """

    password = secure_prompt()

    return uncipher_dict(password, str_vault)