"""Kitt configuration utils"""

import os
import json
import toml

from kitt.logger import panic, debug


class ConfigUtils:
    """ConfigUtils

    Kitt configuration utils.
    """

    @staticmethod
    def mkpath(relative: str) -> str:
        """Create absolute path from relative.

        Args:
            relative (str): relative path to ressource

        Returns:
            str: absolute path using app current folder
        """
        local = os.path.dirname(__file__)
        return os.path.join(local, relative)

    @classmethod
    def load(cls, config_file: str = None) -> dict:
        """Load config from file, override default config

        Args:
            config_file (str, optional): configuration file path. Defaults to None.

        Returns:
            dict: loaded configuration
        """
        custom = {}
        default = None
        default_config_path = cls.mkpath('static/default.toml')
        try:
            if not (default := toml.load(default_config_path)):
                raise toml.TomlDecodeError
        except (toml.TomlDecodeError, FileNotFoundError, IOError):
            panic('Could not load default config file.')

        if not config_file:
            return default

        try:
            if not (custom := toml.load(config_file)):
                raise ValueError

        except (FileNotFoundError, IOError):
            panic('File does not exist or is not readable.')

        except toml.TomlDecodeError:
            if not (custom := json.load(config_file)):
                raise ValueError from toml.TomlDecodeError

        except ValueError:
            panic('File content cannot be properly handled.')

        except Exception as exception:
            debug(exception)
            panic('Error loading config files.')

        # Handle incomplete user config file
        default = cls.update(custom, default)

        return default

    @classmethod
    def update(cls, src: dict, dest: dict) -> dict:
        """
        Deep update dict config `dest' with config `src'
        Make sure it wont overwrite if empty str or list.

        Args:
            src (dict): config to update
            dest (dict): config override

        Returns:
            dict: updated configuration
        """
        for key, value in src.items():
            if key in dest and isinstance(value, dict) and isinstance(dest[key], dict):
                dest[key] = cls.update(src[key], dest[key])
            elif key in dest and value in ['', [], ['']]:
                continue
            else:
                dest[key] = src[key]

        return dest
