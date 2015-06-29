from flask import current_app
from libthumbor.flask import ThumborData
from libthumbor.flask import ThumborField

try:
    from flask_admin.contrib.mongoengine.fields  import MongoFileField, is_empty
    from flask_admin.contrib.mongoengine.typefmt import DEFAULT_FORMATTERS
    from werkzeug.datastructures import FileStorage
    from wtforms.widgets import HTMLString, html_params
    from jinja2 import Markup
    import requests
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
                # Delete image before uploading
                self.delete_img(obj, name)
            if isinstance(self.data, FileStorage) and not is_empty(self.data.stream) and not self._should_delete:
                    self.upload_img(obj, name)

        def delete_img(self, obj, name):
            url = self.get_endpoint()
            requests.delete(url)
            setattr(obj, name, None)

        def upload_img(self, obj, name):
            with current_app.app_context():
                response = requests.post(current_app.config['THUMBOR_IMAGE_ENDPOINT'], media=self.data.read())
                thumbdata = ThumborData(filename=self.data.filename, content_type=self.data.content_type, path=response.headers['location'])
                setattr(obj, name, thumbdata)

        def get_image(self, **kwargs):
            return self.object_data.get_image(**kwargs)

        def get_endpoint(self):
            return str(self.object_data)

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
            'thumb': value.get_image(height=28, width=36),
        })

MY_FORMATTERS = dict(DEFAULT_FORMATTERS) if ADMIN_PRESENT else dict()
MY_FORMATTERS.update({ThumborData: thumbor_image_formatter})
