SKVO docs
=========

SKVO is a portal gathering processed photometry observation obrained by couple of different facilities and instruments. The main idea is to make those data accessible to others.

Behind the scene
~~~~~~~~~~~~~~~~

Behind the scene of SKVO is hidden several different technologies that make it works.
SKVO consist of the following main parts::
    
    Ubuntu 16.04 server
    Python DJango server
    Apache/NGINX server
    MySQL database
    HBase databsae
    OpenTSDB database

Observation data are stored in couple of different locations, depends on data types.

Photometry
~~~~~~~~~~
Data comming from photometric observations consist of three different types and has to be stored in three different locations linked to each other. Observation data consist from the following types:

    - images: processed raw images, converted to one of the following types, and so ``png`` or ``jpeg/jpg``
    - metadata: information about observation and sources data comming from
    - observation data: processed time series data that represents each point of observation

Images (media)
--------------

blah


Metadata
--------

Example of metadata content is shown bellow::

    [
        {
            "observation": {
                "access": {
                    "access": "on_demand"
                },
                "target": {
                    "target": "beta_Lyr",
                    "catalogue": "catalogue_name",
                    "catalogue_value": "catalogue_value",
                    "description": "desc",
                    "right_ascension": "0.1000000000",
                    "declination": "0.2000000000",
                    "target_class": null
                },
                "instrument": {
                    "instrument": "instrument_name",
                    "instrument_uid": "uid_for_instrument",
                    "telescope": "telescope",
                    "camera": "camera",
                    "spectroscope": "spectac",
                    "field_of_view": "10.0000000000",
                    "description": "int desc"
                },
                "facility": {
                    "facility": "facility_name",
                    "facility_uid": "facility_uid",
                    "description": "fac desc"
                },
                "dataid": {
                    "organisation": {
                        "organisation": "organisation_name_like",
                        "organisation_did": "http://organ",
                        "email": "email@google.com"
                    },
                    "title": "data id title",
                    "publisher": "data_id_publisher",
                    "publisher_did": "http://data_id_publisher"
                },
            },
            "bandpass": {
                "bandpass": "bandpass_name",
                "bandpass_uid": "uid_for_band",
                "spectral_band_type": "optical",
                "photometric_system": "johnson"
            },
            "media": "/etc/sys/data",
            "start_date": "2018-05-01T00:00:00Z",
            "end_date": "2018-05-04T00:00:00Z"
        }
    ]


Those data are stored in MySQL database in several differend tables linked to each other by ``foreign keys``.
Each of the table is deffined by the following python classes as object realted object (ORM)::

    Here ORM will come

Uploading process will craete mentioned json and ``POST`` it to the running endpoint ``/api/photometry/metadata``.
On the backend, there is checked which of the incomming model objects already contain desired information and in such case
won't be craeted and which are not stored in database and will be created on fly. In case, new observation is created, unique ``uuid4``
key is assigned and will be returned in response. This uuid is important pointer to the observation and works as foreign key for
time series (observation points, errors and exposure) data stored in OpenTSDB.

Observation (time series) data:
-------------------------------

Observation data basically consist of magnitude, related timestamp, error, exposure and so forth. Those data will be stored in
OpenTSDB. OpenTSDB is **nosql** database engine running on top of HBase nosql database. OpenTSDB was designed to store
time series and subsequently provide efficient way to access them. Data are stored under key called metric. Each of the metric
can carre couple of additional information. Those informations are stored in pairs ``key: value`` and we call them a **tags**.

Observationd data, from the OpenTSDB point of view, can be splited to three different groups. Basically we created a different metrics
carring a necessary informations about ``magnitudes``, ``magnitude errors`` and ``exposure``. The fourt additional metric is neccesery
to store information about and link infrmation to metadata stored in MySQL database.

**Magnitude** for given target object is stored in metric **<target_uid>.<bandpass_uid>.photometry.<version>**, where
``target_uid`` is a unique identfier for target object, ``bandpas_uid`` is a unique identifier for bandpass used during
observation nad ``version`` represent our internal sign for version of data. A given metric also contain a couple of tags, and so
``instrument``, ``target``, ``source``, ``flux_calibration_level``, ``flux_calibration` and ``timeframe_reference_possition``
[explanation will came later]. An exmaple of http import json for OpenTSDB API is following::

    [
        {
            'metric': beta-20Lyr.jonsonU.photometry.v0
            'timestamp': 14038548000
            'value': 12.0,
            'tags':
                {
                    'instrument': ziga.specterX.buda,
                    'target': bet-20Lyr,
                    'source': upjs,
                    'flux_calibration_level': 1,
                    'flux_calibration': abs,
                    "timeframe_reference_possition": barycenter
                }
        }
    ]

You probalby noticed ``-20`` in metric name. OpenTSDB metric allows just specific symbols to be in metric name, so we are necoding
all other symbols to HEX code for given symbol with leading ``-``.


**Magnitude error** for given timestamp and magnitude is stored in similar way as mmagnitude itself. We are using a metric
**<target_uid>.<bandpass_uid>.error.photometry.<version>** with following OpenTSDB tags, and so ``instrument``, ``target`` and ``source``.
An example of metricc json is::

    [
        {
            'metric': beta-20Lyr.jonsonU.error.photometry.v0
            'timestamp': 14038548000
            'value': 0.1,
            'tags':
                {
                    'instrument': ziga.specterX.buda,
                    'target': bet-20Lyr,
                    'source': upjs,
                }
        }
    ]

**Exposure** is stored in the same way as magnitude error, just under different metric name, **<target_uid>.<bandpass_uid>.exposure.photometry.<version>**
and example is bellow::

    [
        {
            'metric': beta-20Lyr.jonsonU.exposure.photometry.v0
            'timestamp': 14038548000
            'value': 60,
            'tags':
                {
                    'instrument': ziga.specterX.buda,
                    'target': bet-20Lyr,
                    'source': upjs,
                    "unit": ?????? think about this tag
                }
        }
    ]


Finally, there is a one more metrics puting together all previous with related metadata in MySQL database. Used metric is
**<target_uid>.<bandpass_uid>.observation_id.photometry.<version>** and all values stored in this metric are just the same ``observation_id``
from database working as a foreign key for relation database.




Upload data flow
~~~~~~~~~~~~~~~~

Expected data struncture on the local storage is like following::

    data
        `- source
                 `- dtype
                         `- imgs
                         |      `- yyyymm
                         |               `- objectuid_yyyymmdd [datetime when observation starts]
                         |                                    `- bandpass_uid
                         |                                                  `- objectuid_yyyymmdd_id.jpeg/png/whatever
                         `- dtables
                                   `- yyyymm
                                            `- objectuid_yyyymmdd [datetime when observation starts]
                                                                  `- bandpass_uid
                                                                                `- objectuid_yyyymmdd_data_id.csv [observation data]
                                                                                `- objectuid_yyyymmdd_meta_id.csv [metaddata]

Uploader script rely on mentioned data structure.
``data`` path on the top of sctruct tree is defined in ``skvo.ini`` configuration file as ``base_path``.
Concrete structure should looks like following one::

    data
        `- upjs
                `- photometry
                            `- imgs
                            |      `- 201802
                            |               `- bet_Lyr_20180217
                            |                                  `- Jonson.U
                            |                                             `- bet_Lyr_20180217_0.png
                            |                                             `- bet_Lyr_20180217_1.png
                            |                                             `- bet_Lyr_20180217_2.png
                            `- dtables
                                       `- 201802
                                                `- bet_Lyr_20180217
                                                                   `- Jonson.U
                                                                              `- bet_Lyr_20180217_data_id.csv
                                                                              `- bet_Lyr_20180217_meta_id.csv

      
During a runtime of the uploader script, following procedures are executed.
First, for given source (institution, facility, whatever you wish), observation target and bandpass,
metadata and observation data tables are loaded as pandas dataframes.

Here is an example of headers and data line from metadata table (<taget_uuid>_<YYYYMMDD>_meta.csv).

Header::

    arget.target,target.catalogue,target.catalogue_value,target.description,target.right_ascension,target.declination,target.target_class,bandpass.bandpass,bandpass.bandpass_uid,bandpass.spectral_band_type,bandpass.photometric_system,instrument.instrument,instrument.instrument_uid,instrument.telescope,instrument.camera,instrument.spectroscope,instrument.field_of_view,instrument.description,facility.facility,facility.facility_uid,facility.description,organisation.organisation,organisation.organisation_did,organisation.email,dataid.title,dataid.publisher,dataid.publisher_did,access.access

Data::

    bet_Lyr,default,bet_Lyr,bet_Lyr description,18.5,33.21,variable,band.johnson.u,johnson.u,optical,sys,instrument.uvw,instrument.uid.uvw,instrument.telescope.uvw,instrument.camera.uvw,instrument.spect.uvw,15,instrument.description,facility.in.upjs,uid.facility.upjs,facility.description.upjs,organisation.upjs,http://organisation.did.upjs,upjs@upjs.com,title.upjs,publisher.upjs,http://publisher_did.upjs,open

Bellow is an example of header and data line of observation data table <taget_uuid>_<YYYYMMDD>_data.csv

Header::

    ts.timestamp,ts.magnitude,ts.magnitude_error,ts.flux_calibration,ts.flux_calibration_level,ts.exposure,ts.timeframe_reference_position

Data::

    2017-12-04 00:00:11,0.25,0.07692307692307693,abs,2,12,heliocenter

Column name convention follow, otherwise uploader script won't work. Transformation function from dataframe to tsdb metrics and
metadata json rely on the mentioned convention.

You have probably noticed, that data in tables are represented as and real comma separated values, so, just use real csv,
not any decimal position same margin files or any different similar bulshits.

When data are loaded to memory, from the given informations a metadata jeson is created. An exmaple of metadata json is shown above
in section `Metadata`_ . Created metadata json is 'POSTed' on listening endpoint of SKVO Django server, and so ``/api/photometry/metadata``.
This endpoint will return a response based on serializer which contain generated uuid4 of observation and databsae observation id.
The observation id is used in observation id metrics which are linkin database metadata and other observation OpenTSDB metrics.

Now observation data are processed. It is mean, all necessary metrics described in `Observation (time series) data:`_ are created.
Basicaly, pandas dataframes are converted to the python list of dicts shown above, no big deal. Finally, all created metrics are
'POSTed' by ``pyopentsdb`` python library on the OpenTSDB HTTP API endpoint, ``/api/put/``.
    


https://netdisk.sk/file/pGtogvTMJ29O_55VLlRtsQ/delete/frvRNgUq
    
Lookup
~~~~~~



