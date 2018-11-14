from copy import copy

from django.db import transaction
from django.core import validators
from rest_framework import serializers, validators

from observation import models

from django.core.exceptions import ValidationError


def validate_not_empty(value):
    if len(str(value)) == 0:
        raise ValidationError("hash cannot be an empty string", params={'value': value})


class CustomModelSerializer(serializers.ModelSerializer):
    def run_validators(self, value):
        for validator in copy(self.validators):
            if isinstance(validator, (validators.UniqueTogetherValidator, validators.UniqueValidator)):
                self.validators.remove(validator)
        super(CustomModelSerializer, self).run_validators(value)


class TargetSerializer(CustomModelSerializer):
    class Meta:
        model = models.Target
        exclude = ('created', )


class BandpassSerializer(CustomModelSerializer):
    class Meta:
        model = models.Bandpass
        exclude = ('created', )
        extra_kwargs = {
            'bandpass_uid': {
                'validators': [validate_not_empty],
            }
        }


class InstrumentSerializer(CustomModelSerializer):
    class Meta:
        model = models.Instrument
        exclude = ('created', )
        extra_kwargs = {
            'instrument_hash': {
                'validators': [validate_not_empty],
            }
        }


class FacilitySerializer(CustomModelSerializer):
    class Meta:
        model = models.Facility
        exclude = ('created', )
        extra_kwargs = {
            'facility_uid': {
                'validators': [validate_not_empty],
            }
        }


class OrganisationSerializer(CustomModelSerializer):
    class Meta:
        model = models.Organisation
        exclude = ('created', )
        extra_kwargs = {
            'organisation_did': {
                'validators': [validate_not_empty],
            }
        }


class AccessRightsSerializer(CustomModelSerializer):
    class Meta:
        model = models.AccessRights
        exclude = ('created',)
        extra_kwargs = {
            'access': {
                'validators': [validate_not_empty],
            }
        }


class DataIdSerializer(CustomModelSerializer):
    organisation = OrganisationSerializer()

    class Meta:
        model = models.DataId
        exclude = ('created', )


class ObservationSerializer(CustomModelSerializer):
    access = AccessRightsSerializer()
    target = TargetSerializer()
    instrument = InstrumentSerializer()
    facility = FacilitySerializer()
    dataid = DataIdSerializer()

    class Meta:
        model = models.Observation
        exclude = ('created', )
        extra_kwargs = {
            'observation_hash': {
                'validators': [validate_not_empty],
            }
        }


class PhotometrySerializer(CustomModelSerializer):
    bandpass = BandpassSerializer()
    observation = ObservationSerializer()

    class Meta:
        model = models.Photometry
        fields = ('observation', 'bandpass', 'media', 'start_date', 'end_date')


class PhotometryCreateSerializer(CustomModelSerializer):
    observation = ObservationSerializer()
    bandpass = BandpassSerializer()

    class Meta:
        model = models.Photometry
        fields = '__all__'

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        with transaction.atomic():
            target, _ = models.Target.objects.get_or_create(**validated_data["observation"].pop("target"))
            bandpass, _ = models.Bandpass.objects.get_or_create(**validated_data.pop("bandpass"))
            instrument, _ = models.Instrument.objects.get_or_create(**validated_data["observation"].pop("instrument"))
            facility, _ = models.Facility.objects.get_or_create(**validated_data["observation"].pop("facility"))
            organisation, _ = models.Organisation.objects.get_or_create(
                **validated_data["observation"]["dataid"].pop("organisation")
            )
            access_rights, _ = models.AccessRights.objects.get_or_create(**validated_data["observation"].pop("access"))
            dataid, _ = models.DataId.objects.get_or_create(
                **dict(**validated_data["observation"].pop("dataid"), organisation=organisation)
            )
            observation, _ = models.Observation.objects.get_or_create(
                access=access_rights, target=target, instrument=instrument, facility=facility, dataid=dataid,
                observation_hash=validated_data["observation"].pop("observation_hash")
            )
            validated_data.pop("observation")
            photometry, _ = models.Photometry.objects.get_or_create(
                **dict(**validated_data, observation=observation, bandpass=bandpass)
            )
            return photometry


class PhotometryCreateManySerializer(serializers.Serializer):
    photometry = PhotometryCreateSerializer(many=True)

    def update(self, instance, validated_data):
        raise NotImplementedError("We don't do that here")

    def create(self, validated_data):
        validated_data = validated_data.pop('photometry')
        return {
            "photometry":
                [PhotometryCreateSerializer(_validated_data).create(_validated_data)
                 for _validated_data in validated_data]
        }
