from flask  import current_app
from jinja2 import Markup
from libthumbor.flask import ThumborField

import requests
import tempfile

ADMIN_PRESENT = False
crypto_url    = None

try:
    from flask_admin.contrib.mongoengine.fields  import MongoFileField, is_empty
    from flask_admin.contrib.mongoengine.typefmt import DEFAULT_FORMATTERS
    from wtforms.widgets import HTMLString, html_params
    from werkzeug.datastructures import FileStorage
    from werkzeug import secure_filename

    ADMIN_PRESENT = True
except ImportError:
    pass

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
            if len(self.object_data) > 0:
                with current_app.app_context():
                    url = urljoin(current_app.config['THUMBOR_HOST'], self.object_data)
                    requests.delete(url)
            setattr(obj, name, None)

        def upload_img(self, obj, name):
            with current_app.app_context():
                files     = { 'media': self.data }
                response  = requests.post(current_app.config['THUMBOR_IMAGE_ENDPOINT'], files=files)
                setattr(obj, name, response.headers['location'])

        def get_image(self, **kwargs):
            with current_app.app_context():
                global crypto_url
                if crypto_url == None:
                    crypto_url = CryptoURL(key=current_app.config['THUMBOR_SECURITY_KEY'])
                if len(self.object_data) > 0:
                    _url = urljoin('{u.scheme}://{u.netloc}'.format(u=urlparse(current_app.config['THUMBOR_HOST'])), crypto_url.generate(image_url='/'.join(self.object_data.split('/')[2:]), **kwargs))
                    return _url
            return ''

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

MY_FORMATTERS = dict(DEFAULT_FORMATTERS) if ADMIN_PRESENT else dict()
MY_FORMATTERS.update({ThumborData: thumbor_image_formatter})
