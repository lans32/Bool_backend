from django.contrib import admin
from app import models

admin.site.register(models.Ask)
admin.site.register(models.AskOperation)
admin.site.register(models.Operation)