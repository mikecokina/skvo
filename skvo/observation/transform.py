from observation import models
from django.forms import model_to_dict


def photometry_samples_df_to_dict(df):
    ret_val = list()
    for i in range(len(df)):
        model = models.get_observation_by_id(uid=df["observation_id"].iloc[i])

        ret_val.append(
            {
                "start_date": df["start_date"].iloc[i],
                "end_date": df["end_date"].iloc[i],
                "observation": {
                    "id": df["observation_id"].iloc[i],
                    "observation_hash": model.observation_hash
                },
                "instrument": dict(
                    **model_to_dict(model.instrument)
                ),
                "dataid": dict(**model_to_dict(model.dataid)),
                "organisation": dict(**model_to_dict(model.dataid.organisation)),
                "facility": dict(**model_to_dict(model.facility)),
                "access_rights": dict(**model_to_dict(model.access)),
                "target": dict(**model_to_dict(model.target)),
                "bandpass": dict(**model_to_dict(models.get_bandpass_by_uid(uid=df["bandpass"].iloc[i]))),
                "samples": df["samples"].iloc[i],
            }
        )
    return ret_val


def photometry_data_df_to_dict(df):
    ret_val = list()
    for i in range(len(df)):
        pass
