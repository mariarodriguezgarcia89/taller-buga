from django.db import models

class TimeStampedModel(models.Model):
    """Abstract base model that adds creation and update timestamps."""

    created_at = models.DateTimeField("creado el", auto_now_add=True)
    updated_at = models.DateTimeField("modificado el", auto_now=True)

    class Meta:
        abstract = True

# Create your models here.
