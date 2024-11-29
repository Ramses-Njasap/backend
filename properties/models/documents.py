from django.db import models


class Document(models.Model):
    property = models.ForeignKey(
        'Property', related_name='documents',
        on_delete=models.CASCADE
    )
    file = models.FileField(upload_to='documents/')
    document_type = models.ForeignKey(
        'DocumentType', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
