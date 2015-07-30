#!/usr/bin/python
# -*- coding: utf-8 -*-
from mongoengine.base  import BaseField
from libthumbor.crypto import CryptoURL

try:
    from werkzeug.datastructures import FileStorage
    from urllib.parse            import urlparse, urljoin
    from flask                   import current_app
    from flask.ext.mongoengine   import *
    from mongoengine             import *

    from flask_admin.contrib.mongoengine.fields import is_empty
    import requests

    crypto_url = None

    class ThumborData(str):
        def __new__(self, content = None, data = None):
            with current_app.app_context():
                if isinstance(data, FileStorage) and not is_empty(data.stream):
                    files    = { 'media': data }
                    response = requests.post(current_app.config['THUMBOR_IMAGE_ENDPOINT'], files=files)
                    content  = response.headers['location']
            return str.__new__(self, content)

        def delete(self, **kwargs):
            with current_app.app_context():
                url = urljoin(current_app.config['THUMBOR_IMAGE_ENDPOINT'], self)
                requests.delete(url)

        def image(self, **kwargs):
            with current_app.app_context():
                global crypto_url
                if crypto_url == None:
                    crypto_url = CryptoURL(key=current_app.config['THUMBOR_SECURITY_KEY'])
                if len(self) > 0:
                    _url = urljoin('{u.scheme}://{u.netloc}'.format(u=urlparse(current_app.config['THUMBOR_HOST'])), crypto_url.generate(image_url='/'.join(self.split('/')[2:]), **kwargs))
                    return _url
            return ''

        def __repr__(self):
            with current_app.app_context():
                return urljoin(current_app.config['THUMBOR_HOST'], self)
            return ''

    class ThumborField(BaseField):
        def validate(self, value):
            if not isinstance(value, str) or (value is None):
                self.error('{0} is not a valid Thumbor data'.format(value))
            return

        def to_python(self, value):
            return ThumborData(value)

except ImportError:
    class ThumborData(str):
        pass

    class ThumborField(BaseField):
        pass
