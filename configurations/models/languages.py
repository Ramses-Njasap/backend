from django.db import models


class Languages(models.Model):
    name = models.CharField(max_length=58, null=False, blank=False)
    code = models.CharField(max_length=10, null=False, blank=False)
    flag = models.TextField()

    class Meta:
        verbose_name = 'Language'
        verbose_name_plural = 'Languages'
    
    def __str__(self):
        return f'{self.flag} {self.code}'