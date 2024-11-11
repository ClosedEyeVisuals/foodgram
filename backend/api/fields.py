import base64

from django.core.files.base import ContentFile
from rest_framework.serializers import ImageField


class Base64ImageField(ImageField):
    """Поле для добавления изображения к объекту."""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            frmt, imgstr = data.split(';base64,')
            ext = frmt.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)
