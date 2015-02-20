from __future__ import print_function

from os import path
import re
import sys

from honcho.compat import shellquote

try:
    import jinja2
except ImportError:
    print("honcho's 'export' command requires the jinja2 package,\n"
          "which you don't appear to have installed.\n"
          "\n"
          "To fix this, install honcho with the 'export' extra selected:\n"
          "\n"
          "    pip install honcho[export]\n",
          file=sys.stderr)
    sys.exit(1)


class BaseExport(object):
    def __init__(self, template_env=None, context=None):
        if template_env is None:
            template_env = _default_template_env()
        self._template_env = template_env
        self.context = context or {}

    def get_template(self, default_path):
        """
        Retrieve the template at the specified path. Returns an instance of
        :py:class:`Jinja2.Template` by default, but may be overridden by
        subclasses.
        """
        try:
            template = self.context.get('template') or default_path
            return self._template_env.get_template(template)
        except jinja2.exceptions.TemplateNotFound:
            template = path.join(self.context.get('template'), default_path)
            return self._template_env.get_template(template)

    def render(self, processes):
        raise NotImplementedError("You must implement a render method.")


def dashrepl(value):
    """
    Replace any non-word characters with a dash.
    """
    patt = re.compile(r'\W', re.UNICODE)
    return re.sub(patt, '-', value)


def _default_template_env():
    env = jinja2.Environment(
        loader=jinja2.ChoiceLoader([
            jinja2.PackageLoader(__name__, 'templates'),
            jinja2.FileSystemLoader(['/', '.']),
        ])
    )
    env.filters['shellquote'] = shellquote
    env.filters['dashrepl'] = dashrepl
    return env
