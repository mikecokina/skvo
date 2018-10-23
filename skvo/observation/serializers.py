from copy import copy

from rest_framework import serializers, validators

from observation import models

"""
json serializer:

{
   "photometry": [
       {
           "observation": {
               "access": "on_demand",
               "target": {
                   "target": "beta_Lyr",
                   "catalogue": "catalogue_name",
                   "catalogue_value": "catalogue_value",
                   "description": "desc",
                   "right_ascension": 0.1,
                   "declination": 0.2,
                   "raget_class": "binary"
               },
               "instrument": {
                   "instrument": "instrument_name",
                   "instrument_uid": "uid_for_instrument",
                   "telescope": "telescope",
                   "camera": "camera",
                   "spectroscope": "spectac",
                   "field_of_view": 10,
                   "description": "int desc"
               },
               "facility": {
                   "facility": "facility_name",
                   "facility_uid": "facility_uid",
                   "description": "fac desc"
               },
               "dataid": {
                   "title": "data id title",
                   "publisher": "data_id_publisher",
                   "publisher_did": "http://data_id_publisher",
                   "organisation": {
                       "organisation": "organisation_name_like",
                       "organisation_did": "http://organ",
                       "email": "email@google.com"
                   }
               }
           },
           "start_date": "2018-05-01T00:00:00",
           "end_date": "2018-05-04T00:00:00",
           "bandpass": {
               "bandpass": "bandpass_name",
               "bandpass_uid": "uid_for_band",
               "spectral_band_type": "optical",
               "photometric_system": "johnson"
           },
           "media": "/etc/sys/data"
       }
   ]
}
"""


class CustomModelSerializer(serializers.ModelSerializer):
    def run_validators(self, value):
        for validator in copy(self.validators):
            if isinstance(validator, validators.UniqueTogetherValidator):
                self.validators.remove(validator)
        super(CustomModelSerializer, self).run_validators(value)


class TargetSerializer(CustomModelSerializer):
    class Meta:
        model = models.Target
        exclude = ('created',)


class BandpassSerializer(CustomModelSerializer):
    class Meta:
        model = models.Bandpass
        exclude = ('created',)


class InstrumentSerializer(CustomModelSerializer):
    class Meta:
        model = models.Instrument
        exclude = ('created',)


class FacilitySerializer(CustomModelSerializer):
    class Meta:
        model = models.Facility
        exclude = ('created',)


class OrganisationSerializer(CustomModelSerializer):
    class Meta:
        model = models.Organisation
        exclude = ('created',)


class AccessRightsSerializer(CustomModelSerializer):
    class Meta:
        model = models.AccessRights
        exclude = ('created', )


class DataIdSerializer(CustomModelSerializer):
    organisation = OrganisationSerializer()

    class Meta:
        model = models.DataId
        exclude = ('created',)


class ObservationSerializer(CustomModelSerializer):
    access = serializers.CharField()
    target = TargetSerializer()
    instrument = InstrumentSerializer()
    facility = FacilitySerializer()
    dataid = DataIdSerializer()

    class Meta:
        model = models.Observation
        exclude = ('created',)


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
        pass
        # todo: add creation logic (copy from view commented code


class PhotometryCreateManySerializer(serializers.Serializer):
    photometry = PhotometryCreateSerializer(many=True)

    def update(self, instance, validated_data):
        raise NotImplementedError("We don't do that here")

    def create(self, validated_data):
        validated_data = validated_data.pop('photometry')
        # todo: add creation logic (copy from view commented code   )
