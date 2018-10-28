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

    example of metadata content is shown bellow::

        [
            {
                "observation": {
                    "id": 5,
                    "access": {
                        "id": 6,
                        "access": "on_demand"
                    },
                    "target": {
                        "id": 6,
                        "target": "beta_Lyr",
                        "catalogue": "catalogue_name",
                        "catalogue_value": "catalogue_value",
                        "description": "desc",
                        "right_ascension": "0.1000000000",
                        "declination": "0.2000000000",
                        "target_class": null
                    },
                    "instrument": {
                        "id": 6,
                        "instrument": "instrument_name",
                        "instrument_uid": "uid_for_instrument",
                        "telescope": "telescope",
                        "camera": "camera",
                        "spectroscope": "spectac",
                        "field_of_view": "10.0000000000",
                        "description": "int desc"
                    },
                    "facility": {
                        "id": 6,
                        "facility": "facility_name",
                        "facility_uid": "facility_uid",
                        "description": "fac desc"
                    },
                    "dataid": {
                        "id": 6,
                        "organisation": {
                            "id": 6,
                            "organisation": "organisation_name_like",
                            "organisation_did": "http://organ",
                            "email": "email@google.com"
                        },
                        "title": "data id title",
                        "publisher": "data_id_publisher",
                        "publisher_did": "http://data_id_publisher"
                    },
                    "observation_uuid": "937cbc6f-3456-4fe4-b845-9c6f463f61bb"
                },
                "bandpass": {
                    "id": 6,
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

Observation (time series) data:
-------------------------------

blah


Upload data flow
----------------

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
                                                                              `- bet_Lyr_20180217_0_data_id.csv
                                                                              `- bet_Lyr_20180217_meta_id.csv

      
    

    
    
    
Internal
~~~~~~~~



