#!/usr/bin/python
# -*- coding: utf-8 -*-
from werkzeug.datastructures import FileStorage
from urllib.parse            import urlparse, urljoin
from types                   import NoneType
from flask                   import current_app
from mongoengine.base        import BaseField
from libthumbor.crypto       import CryptoURL
from flask.ext.mongoengine   import *
from mongoengine             import *

import requests

crypto_url = None

class ThumborData(str):
    def __new__(self, content = None, data = None):
        with current_app.app_context():
            if isinstance(data, FileStorage):
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
        if not isinstance(value, (NoneType, ThumborData, str, list)):
            self.error('{0} is not a valid Thumbor data'.format(value))
        return

    def to_python(self, value):
        return ThumborData(value)
