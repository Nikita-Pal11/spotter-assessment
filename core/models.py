from django.db import models

# Create your models here.
class FuelStop(models.Model):
    truckstop_id = models.IntegerField()
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    rack_id = models.IntegerField()
    price = models.FloatField()
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["lat", "lng"]),
            models.Index(fields=["state"]),
        ]