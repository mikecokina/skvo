import pandas as pd
from django.forms import model_to_dict

from observation import models
from utils import time_utils


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


def photometry_data_df_to_dict(df: pd.DataFrame):
    df["ts.timestamp"] = time_utils.unix_timestamp_to_pd(df["timestamp"], unit='ms')
    df["ts.timestamp"] = time_utils.add_timezone_to_pd_series(df["ts.timestamp"])
    ret_val = dict()
    data = list()

    if not df.empty:
        model = models.get_observation_by_id(uid=df["observation_id"].iloc[0])
        metadata = {
            "start_date": df["ts.timestamp"][df.first_valid_index()],
            "end_date": df["ts.timestamp"][df.last_valid_index()],
            "observation": {
                "id": df["observation_id"].iloc[0],
                "observation_hash": model.observation_hash
            },
            "instrument": dict(**model_to_dict(model.instrument)),
            "bandpass": dict(**model_to_dict(models.get_bandpass_by_uid(uid=df["bandpass"].iloc[0]))),
            "samples": len(df),
            "target": dict(**model_to_dict(model.target)),
            "dataid": dict(**model_to_dict(model.dataid)),
            "organisation": dict(**model_to_dict(model.dataid.organisation)),
            "facility": dict(**model_to_dict(model.facility))
        }

        for i in range(len(df)):
            data.append(
                {
                    "magnitude": df["magnitude"].iloc[i],
                    "error": df["error"].iloc[i],
                    "timestamp": df["ts.timestamp"].iloc[i],
                    "timeframe_reference_position": df["timeframe_reference_position"].iloc[i],
                    "flux_calibration": df["flux_calibration"].iloc[i],
                    "flux_calibration_level": df["flux_calibration_level"].iloc[i],
                    "exposure": df["exposure"].iloc[i]
                }
            )

        ret_val = {
            "metadata": metadata,
            "data": data
        }
    return ret_val
