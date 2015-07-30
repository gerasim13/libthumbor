from flask  import current_app
from jinja2 import Markup

from libthumbor.flask  import ThumborField
from libthumbor.flask  import ThumborData
from libthumbor.crypto import CryptoURL

try:
    from flask_admin.contrib.mongoengine.fields  import MongoFileField
    from flask_admin.contrib.mongoengine.typefmt import DEFAULT_FORMATTERS
    from wtforms.widgets                         import HTMLString, html_params

    ADMIN_PRESENT = True
except ImportError:
    ADMIN_PRESENT = False

if ADMIN_PRESENT:
    class ThumborImageInput(object):
        """
        Renders a file input chooser field.
        """
        template = ("""<div class="%(name)s-thumbnail"><img src="%(thumb)s" />
            <span><input type="checkbox" name="%(marker)s">&nbsp;Удалить</span>
            <a href="#" onclick="cancelFile($('#%(name)s'), '%(thumb)s')" style="display:none">Отменить загрузку</a>
        </div>""")

        def __call__(self, field, **kwargs):
            """
            Renders form widget.
            """
            kwargs.setdefault('id', field.id)
            placeholder = """<div class="{0}-thumbnail"><img />
            <a href="#" onclick="cancelFile($('#{0}'), '')" style="display:none">Отменить загрузку</a>
            </div>""".format(field.name)

            if field.object_data:
                placeholder = self.template % {
                    'thumb': field.get_image(width=80, height=64),
                    'marker': '_{0}-delete'.format(field.name),
                    'name': field.name
                }

            if 'class' in kwargs.keys():
                del kwargs['class']

            return HTMLString('{0}<input {1} onchange="previewFile(this)">'.format(
                placeholder,
                html_params(name=field.name, type='file', **kwargs))
            )

    class ThumborImageField(MongoFileField):
        widget = ThumborImageInput()

        def populate_obj(self, obj, name):
            """
            Manipulates data through Thumbor REST API.
            """
            field = getattr(obj, name, None)
            if field is not None:
                self.delete_img(obj, name)
            if not self._should_delete:
                self.upload_img(obj, name)

        def delete_img(self, obj, name):
            self.object_data.delete()
            setattr(obj, name, None)

        def upload_img(self, obj, name):
            data = ThumborData(data=self.data)
            setattr(obj, name, data)

        def get_image(self, **kwargs):
            return self.object_data.image(**kwargs)

else:
    class ThumborImageInput(object):
        pass

    class ThumborImageField(object):
        pass

def thumbor_image_formatter(view, value):
    """
    Represents content of the field as a thumbnail with link for list view.
    """
    if not value:
        return ''

    return Markup(
        ('<div class="image-thumbnail">' +
            '<a href="%(url)s" target="_blank"><img src="%(thumb)s"/></a>' +
         '</div>') %
        {
            'url': str(value),
            'thumb': value.get_image(height=80, width=64),
        })

THUMBOR_FORMATTERS = dict(DEFAULT_FORMATTERS) if ADMIN_PRESENT else dict()
THUMBOR_FORMATTERS.update({ThumborData: thumbor_image_formatter})
