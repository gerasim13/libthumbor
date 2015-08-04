from .field import ThumborField
from .field import ThumborData

class ThumborImageField: pass
class ThumborImageInput: pass

THUMBOR_FORMATTERS = dict()

try:
    from flask             import Markup,current_app
    from wtforms.widgets   import HTMLString, FileInput, html_params
    from jinja2            import Markup
    from libthumbor.crypto import CryptoURL

    from flask_admin.contrib.mongoengine.fields  import MongoFileField, is_empty
    from flask_admin.contrib.mongoengine.typefmt import DEFAULT_FORMATTERS
    from werkzeug.datastructures                 import FileStorage

    class ThumborImageInput(FileInput):
        """
        Renders a file input chooser field.
        """
        template = Markup("""<div class="%(name)s-thumbnail"><img src="%(thumb)s" />
        <span><input type="checkbox" name="%(marker)s">&nbsp;Удалить</span>
        <a href="#" onclick="cancelFile($('#%(name)s'), '%(thumb)s')" style="display:none">Отменить загрузку</a>
        </div>""")

        placeholder = Markup("""<div class="%(name)s-thumbnail"><img />
        <a href="#" onclick="cancelFile($('#%(name)s'), '')" style="display:none">Отменить загрузку</a>
        </div>""")

        def render(self, field, **kwargs):
            template  = self.template if field.object_data else self.placeholder
            arguments = { 'name' : field.name }

            if field.object_data:
                arguments.update({
                    'thumb': field.get_image(width=80, height=64),
                    'marker': '_{0}-delete'.format(field.name),
                })

            kwargs.setdefault('id', field.id)
            klass       = kwargs.pop('class')
            placeholder = template % arguments

            return HTMLString('{0}<input {1} onchange="previewFile(this)">'.format(
                placeholder,
                html_params(name=field.name, type='file', **kwargs))
            )

        def __call__(self, field, **kwargs):
            if isinstance(field, ThumborImageField):
                return self.render(field, **kwargs)
            return ''

    class ThumborImageField(MongoFileField):
        """
        Manipulates data through Thumbor REST API.
        """
        widget = ThumborImageInput()

        def populate_obj(self, obj, name):
            field  = getattr(obj, name, None)
            upload = isinstance(self.data, FileStorage) and not is_empty(self.data.stream)
            delete = (self._should_delete or upload) and field is not None
            if delete:
                self.delete_img(obj, name)
            if upload:
                self.upload_img(obj, name)

        def upload_img(self, obj, name):
            data = ThumborData(data=self.data)
            setattr(obj, name, data)

        def delete_img(self, obj, name):
            if isinstance(self.object_data, ThumborData):
                self.object_data.delete()
                setattr(obj, name, None)

        def get_image(self, **kwargs):
            if isinstance(self.object_data, ThumborData):
                return self.object_data.image(**kwargs)
            return ''

    def thumbor_image_formatter(view, value):
        """
        Represents content of the field as a thumbnail with link for list view.
        """
        if not value:
            return ''

        template  = ("""<div class="image-thumbnail"><a href="%(url)s" target="_blank"><img src="%(thumb)s"/></a></div>""")
        arguments = { 'url': value.endpoint(), 'thumb': value.image(height=80, width=64) }
        return Markup(template % arguments)

    THUMBOR_FORMATTERS.update(DEFAULT_FORMATTERS)
    THUMBOR_FORMATTERS.update({ThumborData: thumbor_image_formatter})

except ImportError:
    pass
