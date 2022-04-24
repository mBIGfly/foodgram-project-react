import base64
import mimetypes

from django.core.files.base import ContentFile
from rest_framework import serializers


class ImageBase64Field(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            mime_data, image_string = data.split(';base64,')
            image_data = base64.b64decode(image_string)

            mime_type = mime_data.removeprefix('data:')
            extension = mimetypes.MimeTypes().guess_extension(mime_type)

            data = ContentFile(image_data, name=f'temp.{extension}')

        return super().to_internal_value(data)
