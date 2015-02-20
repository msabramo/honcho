from honcho.export.base import BaseExport


class Export(BaseExport):
    def render(self, processes):
        context = self.context
        context['processes'] = processes
        filename = "{0}.conf".format(context['app'])
        template_name = 'supervisord/supervisord.conf'
        jinja2_template = self.get_template(template_name)
        return [(filename, jinja2_template.render(context))]
