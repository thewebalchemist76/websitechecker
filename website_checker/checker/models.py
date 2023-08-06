# website_checker/checker/models.py

from django.contrib.auth.models import User
from django.db import models

class Website(models.Model):
    url = models.URLField()
    is_down = models.BooleanField(default=False)
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.url
