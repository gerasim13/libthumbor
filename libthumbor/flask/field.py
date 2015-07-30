from mongoengine import *
from mongoengine.base import BaseField
from flask.ext.mongoengine import *
from flask import current_app
from urllib.parse import urlparse, urljoin
from libthumbor.crypto import CryptoURL

class ThumborField(BaseField):
    def validate(self, value):
        pass
