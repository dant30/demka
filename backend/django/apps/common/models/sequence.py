from django.db import models


class DocumentSequence(models.Model):
    doc_type = models.CharField(max_length=50, unique=True)
    last_value = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.doc_type}: {self.last_value}"