"""Kitt plugins definition and managment"""

import jinja2

from kitt.config import ConfigUtils
from kitt.logger import panic

def compose(name: str, config: dict) -> str:
    """generic compose method

    Args:
        name (str): plugin name
        config (dict): plugin configuration

    Returns:
       str: dockerfile string block
    """

    templater = ConfigUtils.mkpath(f'static/plugins/{name}.j2')
    try:
        with open(templater, 'r', encoding='utf-8') as file:
            template = file.read()
    except OSError:
        panic(f'Cannot load pluging "{name}" template')

    try:
        template = jinja2.Template(template)
        return template.render(config)
    except jinja2.TemplateError:
        panic(f'Cannot render pluging "{name}" : missing or invalid config data provided')

    raise Exception
