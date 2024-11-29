from django.db import models

from properties.models.homes import Home


class MediaType(models.Model):

    name = models.CharField(max_length=65, null=False, blank=False)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_=True)

    class Meta:
        verbose_name = 'Media Type'
        verbose_name_plural = 'Media Types'


class Media(models.Model):

    class MediaType(models.TextChoices):
        VIDEO = 'VIDEO', 'video'
        IMAGE = 'IMAGE', 'image'

    class MediaFormat(models.TextChoices):
        JPEG = 'JPEG', 'jpeg'
        JPG = 'JPG', 'jpg'
        PNG = 'PNG', 'png'
        TIF = 'TIF', 'tif'
        TIFF = 'TIFF', 'tiff'

        MP3 = 'MP3', 'mp3'
        MP4 = 'MP4', 'mp4'
        MOV = 'MOV', 'mov'
        MKV = 'MKV', 'mkv'
        HEVC = 'HEVC', 'hevc'

    property = models.ForeignKey(
        Home, related_name='media', on_delete=models.CASCADE
    )
    media = models.FileField(upload_to='media/homes/')
    media_type = models.ForeignKey(
        MediaType, on_delete=models.SET_NULL, null=True, blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Media'
        verbose_name_plural = 'Media'

    def __str__(self):
        return self.media.name
