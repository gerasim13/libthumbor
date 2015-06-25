from libthumbor.flask import ThumborImageField

try:
    from flask_mongoengine.wtf import orm
    from flask_admin.contrib.mongoengine.form import CustomModelConverter
    ADMIN_PRESENT = True
except ImportError:
    ADMIN_PRESENT = False

if ADMIN_PRESENT:
    class BackendModelConverter(CustomModelConverter):
        """
        Translates model field to form widget.
        """
        @orm.converts('ThumborField')
        def conv_ThumborField(self, model, field, kwargs):
            return ThumborImageField(**kwargs)
else:
    class BackendModelConverter(object):
        pass
