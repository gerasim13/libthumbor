from mongoengine import *
from mongoengine.base import BaseField
from flask.ext.mongoengine import *
from flask import current_app
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
            global crypto_url
            if crypto_url == None:
                crypto_url = CryptoURL(key=current_app.config['THUMBOR_SECURITY_KEY'])
            if 'path' in self.keys():
                _url = urljoin('{u.scheme}://{u.netloc}'.format(u=urlparse(current_app.config['THUMBOR_IMAGE_ENDPOINT'])), crypto_url.generate(image_url='/'.join(self['path'].split('/')[2:]), **kwargs))
                return _url
        return ''

class ThumborField(BaseField):
    def validate(self, value):
        if isinstance(value, str) or (value is None):
            self.error('{0} is not a valid Thumbor data'.format(value))
        return

    def to_python(self, value):
        value_dict = None
        if 'path' in value:
            temp_val = value['path']
            if 'path' in temp_val:
                value_dict = {'path': value['path']['path']}
            else:
                value_dict = {'path': value['path']}
        else:
            value_dict = {'path': value}
        return ThumborData(**value_dict)
