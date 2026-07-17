from django.conf import settings
from django.db import models


class Paper(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    file = models.FileField(upload_to='papers/')
    filename = models.CharField(max_length=500)
    extracted_text = models.TextField(blank=True)
    analysis = models.JSONField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.filename


class Vocabulary(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='vocabulary')
    word = models.CharField(max_length=255)
    meaning_general = models.TextField(blank=True)
    meaning_context = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Vocabulary'

    def __str__(self):
        return self.word
