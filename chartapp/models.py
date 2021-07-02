from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class Data(models.Model):
    country_name = models.CharField(max_length=200, default='Country Name')
    csv_file = models.FileField(upload_to='country_csvs')

    def __str__(self):
        return f"{self.country_name}"