from django.db import models

# Create your models here.

BANDPASS_SPECTRAL_BEND_TYPES = [
    'RADIO', 'MILLIMETER', 'INFRARED', 'OPTICAL', 'ULTRAVIOLET', 'XRAY', 'GAMMARAY'
]


class Target(models.Model):
    name = models.CharField(max_length=128, null=False)
    catalogue = models.CharField(max_length=128, null=False)
    catalogue_value = models.CharField(max_length=128, null=False)
    description = models.CharField(max_length=128, null=True)
    right_ascension = models.DecimalField(max_digits=20, decimal_places=10, null=False)
    declination = models.DecimalField(max_digits=20, decimal_places=10, null=False)
    target_class = models.CharField(max_length=128, null=True)
    edited = models.DateTimeField(auto_now_add=True)
    created = models.DateTimeField(auto_now_add=True)


class Bandpass(models.Model):
    bandpass = models.CharField(max_length=32, null=False)
    spectral_bend_type = models.CharField(choices=BANDPASS_SPECTRAL_BEND_TYPES, null=False)
    photometric_system = models.CharField(max_length=32, null=False)
    unique_identifier = models.CharField(max_length=32, null=False)
    edited = models.DateTimeField(auto_now_add=True)
    created = models.DateTimeField(auto_now_add=True)


class Observation(models.Model):
    target_id = models.ForeignKey(to=Target, on_delete=models.PROTECT)
    bandpass_id = models.ForeignKey(to=Bandpass, on_delete=models.PROTECT)
    instrument_id = models.ForeignKey(to=Instrument, on_delete=models.PROTECT)
    facility_id = models.ForeignKey(to=Facility, on_delete=models.PROTECT)
    edited = models.DateTimeField(auto_now_add=True)
    created = models.DateTimeField(auto_now_add=True)


class Facility(models.Model):
    name = models.CharField(max_length=128, null=False)
    description = models.CharField(max_length=256, null=True)
    edited = models.DateTimeField(auto_now_add=True)
    created = models.DateTimeField(auto_now_add=True)


class Instrument(models.Model):
    name = models.CharField(max_length=64, null=False)
    telescope = models.CharField(max_length=64, null=False)
    camera = models.CharField(max_length=64, null=False)
    filed_of_view = models.DecimalField(max_digits=20, decimal_places=10, null=False)
    description = models.CharField(max_length=256, null=True)
    edited = models.DateTimeField(auto_now_add=True)
    created = models.DateTimeField(auto_now_add=True)


class DataId(models.Model):
    title = models.CharField(max_length=32, null=False)
    publisher = models.CharField(max_length=128, null=False)
    publisher_did = models.CharField(max_length=128, null=False)
    organisation_id = models.ForeignKey(to=Observation, on_delete=models.PROTECT)
    edited = models.DateTimeField(auto_now_add=True)
    created = models.DateTimeField(auto_now_add=True)


class Organisation(models.Model):
    organisation = models.CharField(max_length=128, null=False)
    organisation_did = models.CharField(max_length=128, null=False)
    email = models.CharField(max_length=128, null=False)
    edited = models.DateTimeField(auto_now_add=True)
    created = models.DateTimeField(auto_now_add=True)
