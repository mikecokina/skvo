from django.db import models

# Create your models here.

BANDPASS_SPECTRAL_BEND_TYPES = [
    'RADIO', 'MILLIMETER', 'INFRARED', 'OPTICAL', 'ULTRAVIOLET', 'XRAY', 'GAMMARAY'
]

DTYPES = ["photomery", "spectroscopy"]
ACCESS_RIGHT  = ["open", "on_demand", "restricted"]


class Target(models.Model):
    target = models.CharField(max_length=128, null=False)
    catalogue = models.CharField(max_length=128, null=False)
    catalogue_value = models.CharField(max_length=128, null=False)
    description = models.CharField(max_length=128, null=True)
    right_ascension = models.DecimalField(max_digits=20, decimal_places=10, null=False)
    declination = models.DecimalField(max_digits=20, decimal_places=10, null=False)
    target_class = models.CharField(max_length=128, null=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('catalogue', 'catalogue_value')


class Bandpass(models.Model):
    bandpass = models.CharField(max_length=32, null=False)
    bandpass_uid = models.CharField(max_length=32, null=False, unique=True)
    spectral_band_type = models.CharField(choices=BANDPASS_SPECTRAL_BEND_TYPES, null=False)
    photometric_system = models.CharField(max_length=32, null=False)
    created = models.DateTimeField(auto_now_add=True)


class Instrument(models.Model):
    instrument = models.CharField(max_length=64, null=False)
    instrument_uid = models.CharField(max_length=128, null=False, unique=True)
    telescope = models.CharField(max_length=64, null=False)
    camera = models.CharField(max_length=64, null=False)
    spectroscope = models.CharField(max_length=64, null=True)
    filed_of_view = models.DecimalField(max_digits=20, decimal_places=10, null=False)
    description = models.CharField(max_length=256, null=True)
    created = models.DateTimeField(auto_now_add=True)


class Facility(models.Model):
    facility = models.CharField(max_length=128, null=False)
    facility_uid = models.CharField(max_length=128, null=False, unique=True)
    description = models.CharField(max_length=256, null=True)
    created = models.DateTimeField(auto_now_add=True)


class Organisation(models.Model):
    organisation = models.CharField(max_length=128, null=False)
    organisation_did = models.CharField(max_length=128, null=False, unique=True)
    email = models.CharField(max_length=128, null=False)
    created = models.DateTimeField(auto_now_add=True)


class DataId(models.Model):
    title = models.CharField(max_length=32, null=False)
    publisher = models.CharField(max_length=128, null=False)
    publisher_did = models.CharField(max_length=128, null=False)
    organisation_id = models.ForeignKey(to=Observation, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)


class Observation(models.Model):
    observation_uuid = models.CharField(max_length=128, null=False)
    access_id = models.ForeignKey(to=AccessRights, on_delete=models.PROTECT)
    target_id = models.ForeignKey(to=Target, on_delete=models.PROTECT)
    instrument_id = models.ForeignKey(to=Instrument, on_delete=models.PROTECT)
    facility_id = models.ForeignKey(to=Facility, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)


class AccessRights(models.Model):
    access = models.CharField(choices=ACCESS_RIGHT, null=False)
    created = models.DateTimeField(auto_now_add=True)


class Photometry(models.Model):
    observatiod_id = models.ForeignKey(to=Observation, on_delete=models.PROTECT)
    bandpass_id = models.ForeignKey(to=Bandpass, on_delete=models.PROTECT)
    media = models.CharField(max_length=256, null=False)
    created = models.DateTimeField(auto_now_add=True)


class Spectroscopy(models.Model):
    observation_id = models.ForeignKey(to=Observation, on_delete=models.PROTECT)
    target_id = models.ForeignKey(to=Target, on_delete=models.PROTECT)
    media = models.CharField(max_length=256, null=False)
    created = models.DateTimeField(auto_now_add=True)
