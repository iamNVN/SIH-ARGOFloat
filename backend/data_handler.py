from ftplib import FTP
from pathlib import Path
from tqdm import tqdm
import xarray as xr
import pandas as pd
import numpy as np
import json
from sqlalchemy import create_engine, URL
import sqlalchemy


FTP_HOST = "ftp.ifremer.fr"
FTP_DIR  = "/ifremer/argo/dac/aoml/1900683"
LOCAL_DIR = Path("../argo_sample")
NUM_FILES = 5

LOCAL_DIR.mkdir(parents=True, exist_ok=True)

def download_small_subset():
    ftp = FTP(FTP_HOST)
    ftp.login()
    print(f"Connected to {FTP_HOST}")


    ftp.cwd(FTP_DIR)
    files = ftp.nlst()
    print(f"Total files found: {len(files)}")

    nc_files = [f for f in files if f.endswith(".nc")]
    print(f"NetCDF files: {len(nc_files)} (downloading first {NUM_FILES})")

    for fname in tqdm(nc_files[:NUM_FILES], desc="Downloading"):
        local_path = LOCAL_DIR / fname
        with open(local_path, "wb") as f:
            ftp.retrbinary(f"RETR {fname}", f.write)

    ftp.quit()
    print(f"Downloaded {NUM_FILES} files to {LOCAL_DIR.resolve()}")


DATA_DIR = "D:/SIH-ARGOFloat/argo_sample"
meta_file    = r"D:\SIH-ARGOFloat\argo_sample\1900683_meta.nc"
traj_file    = DATA_DIR + "/1900683_Rtraj.nc"
tech_file    = DATA_DIR + "/1900683_tech.nc"
profile_file = DATA_DIR + "/1900683_prof.nc"

meta_ds = xr.open_dataset(meta_file)
traj_ds = xr.open_dataset(traj_file, decode_timedelta=True)
prof_ds = xr.open_dataset(profile_file)
tech_ds = xr.open_dataset(tech_file)

def to_scalar_or_list(var, sep=", "):
    vals = var.values
    if vals.size == 1:
        return str(vals.item())
    else:
        unique_vals = list(dict.fromkeys(pd.Series(vals.ravel()).dropna().tolist()))
        return sep.join(map(str, unique_vals))
    
def clean_bytes(val):
    if isinstance(val, (bytes, bytearray)):
        return val.decode("utf-8", errors="ignore").strip()
    return val

def safe_json(val):
    try:
        return json.dumps(
            np.nan_to_num(val, nan=None).tolist()
            if isinstance(val, (np.ndarray, list))
            else str(val)
        )
    except Exception:
        return json.dumps(str(val))

meta_dict = {
    "platform_number":       to_scalar_or_list(meta_ds.PLATFORM_NUMBER),
    "project_name":          to_scalar_or_list(meta_ds.PROJECT_NAME),
    "data_centre":           to_scalar_or_list(meta_ds.DATA_CENTRE),
    "pi_name":               to_scalar_or_list(meta_ds.PI_NAME),
    "float_owner":           to_scalar_or_list(meta_ds.FLOAT_OWNER),
    "operating_institution": to_scalar_or_list(meta_ds.OPERATING_INSTITUTION),
    "launch_date":           to_scalar_or_list(meta_ds.LAUNCH_DATE),
    "launch_latitude":       to_scalar_or_list(meta_ds.LAUNCH_LATITUDE),
    "launch_longitude":      to_scalar_or_list(meta_ds.LAUNCH_LONGITUDE),
    "deployment_platform":   to_scalar_or_list(meta_ds.DEPLOYMENT_PLATFORM),
    "deployment_cruise_id":  to_scalar_or_list(meta_ds.DEPLOYMENT_CRUISE_ID),
    "end_mission_date":      to_scalar_or_list(meta_ds.END_MISSION_DATE),
    "end_mission_status":    to_scalar_or_list(meta_ds.END_MISSION_STATUS),

    # Arrays of sensors/parameters
    "sensor":                to_scalar_or_list(meta_ds.SENSOR),
    "sensor_maker":          to_scalar_or_list(meta_ds.SENSOR_MAKER),
    "sensor_model":          to_scalar_or_list(meta_ds.SENSOR_MODEL),
    "parameter":             to_scalar_or_list(meta_ds.PARAMETER),
    "parameter_units":       to_scalar_or_list(meta_ds.PARAMETER_UNITS),
    "parameter_accuracy":    to_scalar_or_list(meta_ds.PARAMETER_ACCURACY),
    "config_parameter_name": to_scalar_or_list(meta_ds.CONFIG_PARAMETER_NAME),
    "config_parameter_value":to_scalar_or_list(meta_ds.CONFIG_PARAMETER_VALUE),
}

meta_df = pd.DataFrame([dict(list(meta_dict.items())[:100])])
meta_df = meta_df.applymap(clean_bytes)

profile_dict = {
    # --- Identification ---
    "platform_number":      to_scalar_or_list(prof_ds.PLATFORM_NUMBER),
    "project_name":         to_scalar_or_list(prof_ds.PROJECT_NAME),
    "pi_name":              to_scalar_or_list(prof_ds.PI_NAME),
    "data_centre":          to_scalar_or_list(prof_ds.DATA_CENTRE),
    "cycle_number":         to_scalar_or_list(prof_ds.CYCLE_NUMBER),
    "direction":            to_scalar_or_list(prof_ds.DIRECTION),
    "platform_type":        to_scalar_or_list(prof_ds.PLATFORM_TYPE),
    "wmo_inst_type":        to_scalar_or_list(prof_ds.WMO_INST_TYPE),

    # --- Time & Location ---
    "juld":                 to_scalar_or_list(prof_ds.JULD),
    "latitude":             to_scalar_or_list(prof_ds.LATITUDE),
    "longitude":            to_scalar_or_list(prof_ds.LONGITUDE),
    "positioning_system":   to_scalar_or_list(prof_ds.POSITIONING_SYSTEM),

    # --- Profile Quality ---
    "juld_qc":              to_scalar_or_list(prof_ds.JULD_QC),
    "position_qc":          to_scalar_or_list(prof_ds.POSITION_QC),
    "profile_pres_qc":      to_scalar_or_list(prof_ds.PROFILE_PRES_QC),
    "profile_temp_qc":      to_scalar_or_list(prof_ds.PROFILE_TEMP_QC),
    "profile_psal_qc":      to_scalar_or_list(prof_ds.PROFILE_PSAL_QC),

    # --- Measurement Data (always lists) ---
    "pres":                 prof_ds.PRES.values.tolist(),
    "pres_qc":              prof_ds.PRES_QC.values.tolist(),
    "pres_adjusted":        prof_ds.PRES_ADJUSTED.values.tolist(),
    "temp":                 prof_ds.TEMP.values.tolist(),
    "temp_qc":              prof_ds.TEMP_QC.values.tolist(),
    "temp_adjusted":        prof_ds.TEMP_ADJUSTED.values.tolist(),
    "psal":                 prof_ds.PSAL.values.tolist(),
    "psal_qc":              prof_ds.PSAL_QC.values.tolist(),
    "psal_adjusted":        prof_ds.PSAL_ADJUSTED.values.tolist(),

    # --- Sampling / Calibration ---
    "vertical_sampling_scheme": to_scalar_or_list(prof_ds.VERTICAL_SAMPLING_SCHEME),
    "parameter":                to_scalar_or_list(prof_ds.PARAMETER),
    "scientific_calib_comment": to_scalar_or_list(prof_ds.SCIENTIFIC_CALIB_COMMENT),
}

profile_df = pd.DataFrame([dict(list(profile_dict.items())[:100])])
profile_df = profile_df.applymap(clean_bytes)
for col in ["pres","pres_qc","pres_adjusted",
            "temp","temp_qc","temp_adjusted",
            "psal","psal_qc","psal_adjusted"]:
    profile_df[col] = profile_df[col].apply(safe_json)


trajectory_dict = {
    # --- Identification ---
    "platform_number":      to_scalar_or_list(traj_ds.PLATFORM_NUMBER),
    "project_name":         to_scalar_or_list(traj_ds.PROJECT_NAME),
    "pi_name":              to_scalar_or_list(traj_ds.PI_NAME),
    "data_centre":          to_scalar_or_list(traj_ds.DATA_CENTRE),
    "platform_type":        to_scalar_or_list(traj_ds.PLATFORM_TYPE),
    "wmo_inst_type":        to_scalar_or_list(traj_ds.WMO_INST_TYPE),

    # --- Time & Location ---
    "juld":                 to_scalar_or_list(traj_ds.JULD),
    "juld_adjusted":        to_scalar_or_list(traj_ds.JULD_ADJUSTED),
    "latitude":             to_scalar_or_list(traj_ds.LATITUDE),
    "longitude":            to_scalar_or_list(traj_ds.LONGITUDE),
    "position_accuracy":    to_scalar_or_list(traj_ds.POSITION_ACCURACY),
    "positioning_system":   to_scalar_or_list(traj_ds.POSITIONING_SYSTEM),

    # --- Cycle Info ---
    "cycle_number":         to_scalar_or_list(traj_ds.CYCLE_NUMBER),
    "cycle_number_adjusted":to_scalar_or_list(traj_ds.CYCLE_NUMBER_ADJUSTED),
    "config_mission_number":to_scalar_or_list(traj_ds.CONFIG_MISSION_NUMBER),

    # --- Core Measurements ---
    "pres":                 to_scalar_or_list(traj_ds.PRES),
    "pres_adjusted":        to_scalar_or_list(traj_ds.PRES_ADJUSTED),
    "temp":                 to_scalar_or_list(traj_ds.TEMP),
    "temp_adjusted":        to_scalar_or_list(traj_ds.TEMP_ADJUSTED),
    "psal":                 to_scalar_or_list(traj_ds.PSAL),
    "psal_adjusted":        to_scalar_or_list(traj_ds.PSAL_ADJUSTED),

    # --- Quality Flags ---
    "pres_qc":              to_scalar_or_list(traj_ds.PRES_QC),
    "temp_qc":              to_scalar_or_list(traj_ds.TEMP_QC),
    "psal_qc":              to_scalar_or_list(traj_ds.PSAL_QC),
    "position_qc":          to_scalar_or_list(traj_ds.POSITION_QC),
    "juld_qc":              to_scalar_or_list(traj_ds.JULD_QC),

    # --- Optional Mission Events ---
    "juld_descent_start":   to_scalar_or_list(traj_ds.JULD_DESCENT_START),
    "juld_ascent_end":      to_scalar_or_list(traj_ds.JULD_ASCENT_END),
    "juld_transmission_start": to_scalar_or_list(traj_ds.JULD_TRANSMISSION_START),
    "juld_transmission_end":   to_scalar_or_list(traj_ds.JULD_TRANSMISSION_END),
}

trajectory_df = pd.DataFrame([dict(list(trajectory_dict.items())[:100])])
trajectory_df = trajectory_df.applymap(clean_bytes)

tech_dict = {
    # --- Identification ---
    "platform_number":          to_scalar_or_list(tech_ds.PLATFORM_NUMBER),
    "data_centre":              to_scalar_or_list(tech_ds.DATA_CENTRE),

    # --- Version / Metadata ---
    "data_type":                to_scalar_or_list(tech_ds.DATA_TYPE),
    "format_version":           to_scalar_or_list(tech_ds.FORMAT_VERSION),
    "handbook_version":         to_scalar_or_list(tech_ds.HANDBOOK_VERSION),

    # --- Timestamps ---
    "date_creation":            to_scalar_or_list(tech_ds.DATE_CREATION),
    "date_update":              to_scalar_or_list(tech_ds.DATE_UPDATE),

    # --- Mission Tracking ---
    "cycle_number":             to_scalar_or_list(tech_ds.CYCLE_NUMBER),

    # --- Technical Parameters ---
    "technical_parameter_name": to_scalar_or_list(tech_ds.TECHNICAL_PARAMETER_NAME),
    "technical_parameter_value":to_scalar_or_list(tech_ds.TECHNICAL_PARAMETER_VALUE),
}
tech_df = pd.DataFrame([dict(list(tech_dict.items())[:100])])
tech_df = tech_df.applymap(clean_bytes)

def main():
    url = URL.create(
        "postgresql+psycopg2",
        username="postgres",
        password="admin",
        host="127.0.0.1",
        port=5432,
        database="argo"
    )

    engine = create_engine(url)

    meta_df.to_sql("argo_metadata", engine, if_exists="replace", index=False)
    trajectory_df.to_sql("argo_trajectory", engine, if_exists="replace", index=False)
    tech_df.to_sql("argo_technical", engine, if_exists="replace", index=False)
    profile_df.to_sql(
    "argo_profile",
    engine,
    if_exists="replace",
    index=False,
    dtype={"pres": sqlalchemy.types.JSON,
           "temp": sqlalchemy.types.JSON,
           "psal": sqlalchemy.types.JSON}
)

    print("DataFrames successfully loaded into PostgreSQL tables.")

if __name__ == "__main__":
    main()
