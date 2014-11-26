import logging
import os
from collections import defaultdict, namedtuple
from pkg_resources import resource_filename
from ..helpers import TestCase
from ..helpers import get_procfile

from honcho import compat, environ
from honcho.export.supervisord import Export


Options = namedtuple("Options", ("app", "app_root", "format", "log", "port", "user", "shell", "location"))

DEFAULT_OPTIONS = Options(app="app", app_root="/path/to/app", format="supervisord", log="/path/to/log",
                          port=5000, user=os.getlogin(), shell="/usr/local/shell", location="/path/to/export")

DEFAULT_ENV = {}

DEFAULT_CONCURRENCY = defaultdict(lambda: 1)

logger = logging.getLogger(__name__)


def get_render(procfile, options, env, concurrency, *args, **kwargs):
    processes = environ.expand_processes(procfile.processes,
                                         concurrency=concurrency,
                                         env=env,
                                         port=options.port)
    context = {
        'app': options.app,
        'app_root': options.app_root,
        'log': options.log,
        'shell': options.shell,
        'user': options.user or options.app,
        'template': kwargs.get('template'),
    }

    export = Export()
    return export.render(processes, context)


class TestExportSupervisord(TestCase):

    def test_supervisord_export(self):
        procfile = get_procfile("Procfile.simple")
        render = get_render(procfile, DEFAULT_OPTIONS, DEFAULT_ENV, DEFAULT_CONCURRENCY)

        self.assertEqual(1, len(render))
        (fname, contents), = render

        parser = compat.ConfigParser()
        parser.readfp(compat.StringIO(contents))

        section = "program:foo-1"

        self.assertTrue(parser.has_section(section))
        self.assertEqual(DEFAULT_OPTIONS.user, parser.get(section, "user"))
        self.assertEqual("{0} -c 'python simple.py'"
                         .format(DEFAULT_OPTIONS.shell),
                         parser.get(section, "command"))

    def test_supervisord_export_custom_template(self):
        procfile = get_procfile("Procfile.simple")
        template_path = resource_filename('honcho', 'test/fixtures/custom_supervisord.conf')
        render = get_render(
            procfile=procfile,
            options=DEFAULT_OPTIONS,
            env=DEFAULT_ENV,
            concurrency=DEFAULT_CONCURRENCY,
            template=template_path)

        self.assertEqual(1, len(render))
        (fname, contents), = render

        parser = compat.ConfigParser()
        parser.readfp(compat.StringIO(contents))

        section = "program:foo-1"

        self.assertTrue(parser.has_section(section))
        self.assertEqual(DEFAULT_OPTIONS.user, parser.get(section, "user"))
        self.assertEqual("{0} -c 'python simple.py'"
                         .format(DEFAULT_OPTIONS.shell),
                         parser.get(section, "command"))
        expected_text = ('# Generated from custom template: '
                         'honcho/test/fixtures/custom_supervisord.conf')
        self.assertTrue(expected_text in contents,
                        'Did not find expected text %r in rendered config:\n%s'
                        % (expected_text, contents))

    def test_supervisord_concurrency(self):
        procfile = get_procfile("Procfile.simple")
        render = get_render(procfile, DEFAULT_OPTIONS, DEFAULT_ENV, {"foo": 4})

        self.assertEqual(1, len(render))
        (fname, contents), = render
        logger.debug('contents =\n%s', contents)

        parser = compat.ConfigParser()
        parser.readfp(compat.StringIO(contents))

        for job_index in compat.xrange(4):
            section = "program:foo-{0}".format(job_index + 1)
            self.assertTrue(parser.has_section(section))
            self.assertEqual('PORT={0}'
                             .format(DEFAULT_OPTIONS.port + job_index),
                             parser.get(section, "environment"))

        self.assertEqual(
            parser.get("group:app", "programs"),
            ",".join("foo-{0}".format(i + 1) for i in compat.xrange(4)))
