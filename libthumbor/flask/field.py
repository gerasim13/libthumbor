from mongoengine import *
from mongoengine.base import BaseField
from flask.ext.mongoengine import *
from flask import current_app
from werkzeug.datastructures import FileStorage
from wtforms.widgets import HTMLString, html_params
from urllib.parse import urlparse, urljoin
from libthumbor.crypto import CryptoURL

crypto_url = None

class ThumborData(dict):
    """
    A dictionary with a string (absolute URL) representation.
    """
    def __init__(self, **kwargs):
        self.update(kwargs)

    def __repr__(self):
        with current_app.app_context():
            if 'path' in self.keys():
                return urljoin(current_app.config['THUMBOR_IMAGE_ENDPOINT'], self['path'])
        return ''

    def __str__(self):
        return self.__repr__()

    def get_image(self, **kwargs):
        with current_app.app_context():
            if crypto_url == None:
                crypto_url = CryptoURL(key=current_app.config['THUMBOR_SECURITY_KEY'])
            if 'path' in self.keys():
                return urljoin('{u.scheme}://{u.netloc}'.format(u=urlparse(current_app.config['THUMBOR_IMAGE_ENDPOINT'])),
                crypto_url.generate(image_url='/'.join(self['path'].split('/')[2:]), **kwargs))
        return ''

class ThumborField(BaseField):
    def validate(self, value):
        if isinstance(value, str) or (value is None):
            self.error('{0} is not a valid Thumbor data'.format(value))
        return

    def to_python(self, value):
        return ThumborData(**value)

class ThumborImageInput(object):
    """
    Renders a file input chooser field.
    """
    template = ("""    <div class="%(name)s-thumbnail">
      <img src="%(thumb)s" />
      <span><input type="checkbox" name="%(marker)s">&nbsp;Удалить</span>
      <a href="#" onclick="cancelFile($('#%(name)s'), '%(thumb)s')" style="display:none">Отменить загрузку</a>
    </div>""")

    def __call__(self, field, **kwargs):
        """
        Renders form widget.
        """
        kwargs.setdefault('id', field.id)
        placeholder = """    <div class="{0}-thumbnail">
      <img />
      <a href="#" onclick="cancelFile($('#{0}'), '')" style="display:none">Отменить загрузку</a>
    </div>""".format(field.name)

        if field.object_data:
            placeholder = self.template % {
                'thumb': field.get_image(width=80, height=64),
                'marker': '_{0}-delete'.format(field.name),
                'name': field.name,
            }

        del kwargs['class']
        return HTMLString('{0}<input {1} onchange="previewFile(this)">'.format(
            placeholder,
            html_params(name=field.name, type='file', **kwargs))
        )


class ThumborImageField(MongoImageField):
    widget = ThumborImageInput()

    def get_image(self, **kwargs):
        return self.object_data.get_image(**kwargs)

    def get_endpoint(self):
        return str(self.object_data)

    def populate_obj(self, obj, name):
        """
        Manipulates data through Thumbor REST API.
        """
        field = getattr(obj, name, None)
        if self._should_delete:
            # delete
            if field is not None:
                url = self.get_endpoint()
                requests.delete(url)
                setattr(obj, name, None)
            return

        if isinstance(self.data, FileStorage) and not is_empty(self.data.stream):
            with current_app.app_context():
                if field is None:
                    # create
                    response = requests.post(current_app.config['THUMBOR_IMAGE_ENDPOINT'],
                                             data=self.data.read(),
                                             headers={'Content-type': self.data.content_type})
                    setattr(obj,
                            name,
                            ThumborData(filename=self.data.filename,
                                        content_type=self.data.content_type,
                                        path=response.headers['location']))
                else:
                    # update (delete, then create)
                    url = self.get_endpoint()
                    requests.delete(url)
                    response = requests.post(current_app.config['THUMBOR_IMAGE_ENDPOINT'],
                                             data=self.data.read(),
                                             headers={'Content-type': self.data.content_type})
                    setattr(obj,
                            name,
                            ThumborData(filename=self.data.filename,
                                        content_type=self.data.content_type,
                                        path=response.headers['location']))


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

MY_FORMATTERS = dict(DEFAULT_FORMATTERS)
MY_FORMATTERS.update({ThumborData: thumbor_image_formatter})
