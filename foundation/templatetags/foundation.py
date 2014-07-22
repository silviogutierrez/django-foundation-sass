from django import template
from django.core.cache import cache

register = template.Library()


@register.tag
def sass(parser, token):
    nodelist = parser.parse(('endsass',))
    parser.delete_first_token()
    return SASSNode(nodelist)


class SASSNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        filenames = output.strip().split("\n")

        from django.contrib.staticfiles import finders
        from django.conf import settings
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        import os
        import re
        import sass

        foundation_path = finders.find('scss/foundation.scss')
        foundation_dir = os.path.dirname(foundation_path)

        # include_paths = [os.path.join(d, 'scss') for d in settings.STATICFILES_DIRS] + [foundation_dir.encode('utf-8'),]
        include_paths = []
        for finder in finders.get_finders():
            for path, storage in finder.list([]):
                path_dir = os.path.dirname(storage.path(path)).encode('utf-8')

                if path_dir not in include_paths:
                    include_paths.append(path_dir)

        for f in filenames:
            full_href = re.search('href="(.*)"', f).groups()[0]
            if full_href.endswith('.scss'):
                cache_key = "sass_%s" % full_href
                cached = cache.get(cache_key)

                if not cached or settings.DEBUG:
                    if full_href.startswith(settings.STATIC_URL):
                        href = full_href.replace(settings.STATIC_URL, '')
                        destination = href.replace('scss', 'css')
                        absolute_path = finders.find(href)

                    elif full_href.startswith(settings.MEDIA_ROOT):
                        destination = full_href.replace(settings.MEDIA_ROOT, '').replace('scss', 'css')
                        absolute_path = full_href

                    content = sass.compile(filename=absolute_path.encode('utf-8'), include_paths=include_paths)
                    if default_storage.exists(destination):
                        default_storage.delete(destination)
                    default_storage.save(destination, ContentFile(content))
                    cached = os.path.join(settings.MEDIA_URL, destination)
                    cache.set(cache_key, cached, None)

                output = output.replace(full_href, cached)

        return output


@register.filter
def foundation_formset_iterator(formset):
    sorted_list = []
    tail = []

    for form in formset:
        if 'ORDER' in form:
            weight = form['ORDER'].value()

            if weight:
                sorted_list.append((weight, form))
            else:
                tail.append(form)
        else:
            tail.append(form)

    sorted_list.sort()

    for _, form in sorted_list:
        yield form
    for form in tail:
        yield form
    yield formset.empty_form


@register.filter
def foundation_widget_type(field):
    return field.field.widget.__class__.__name__.lower()


@register.filter
def foundation_field(field):
    if field.errors:
        field.field.help_text = field.errors[0]

    return field


@register.inclusion_tag('foundation/field.html')
def foundation_field(field, columns='large-12', placeholder=False):
    if placeholder:
        field.field.widget.attrs['placeholder'] = field.label

    return {
        'field': field,
        'columns': columns,
        'placeholder': placeholder,
    }
    return field


@register.inclusion_tag('foundation/form.html')
def foundation_form(form=None, columns=None, button=False):
    # Empty forms are allowed.
    if not form:
        return {
            'form': {
                'visible_fields': [],
                'hidden_fields': [],
                'non_field_errors': [],
                'errors': [],
            },
            'button': button,
        }
    if columns:
        split_columns = columns.split(',')
    else:
        split_columns = []

    for i, f in enumerate(form.visible_fields()):
        if i < len(split_columns):
            f.field.columns = 'medium-%s' % split_columns[i]
        else:
            f.field.columns = 'medium-12'

    return {
        'form': form,
        'button': button,
    }


@register.inclusion_tag('foundation/partial_form.html')
def foundation_partial_form(form, columns):
    split_columns = columns.split(',')

    fields = []
    for c in split_columns:
        split = c.split(':')

        if len(split) == 2:
            field_name, size = split
        else:
            field_name, size = split[0], 12

        field = form[field_name]
        field.field.columns = 'medium-%s' % size
        fields.append(field)

    return {
        'form': form,
        'fields': fields,
    }
