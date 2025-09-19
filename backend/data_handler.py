from ftplib import FTP
from pathlib import Path
from tqdm import tqdm
import xarray as xr
import pandas as pd
import numpy as np
import json
from sqlalchemy import create_engine, URL
from utils.logger import logger

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


DATA_DIR = Path("../argo_sample")
meta_file    = DATA_DIR / "1900683_meta.nc"
traj_file    = DATA_DIR / "1900683_Rtraj.nc"
tech_file    = DATA_DIR / "1900683_tech.nc"
profile_file = DATA_DIR / "1900683_prof.nc"

meta_ds = xr.open_dataset(meta_file)
traj_ds = xr.open_dataset(traj_file, decode_timedelta=True)
prof_ds = xr.open_dataset(profile_file)
tech_ds = xr.open_dataset(tech_file)

    
def clean_bytes_like_string(val):
    if isinstance(val, (bytes, bytearray)):
        try:
            val = val.decode("utf-8")
        except Exception:
            val = str(val)
    if isinstance(val, str):
        s = val.strip()
        if (s.startswith("b'") and s.endswith("'")) or (s.startswith('b"') and s.endswith('"')):
            s = s[2:-1].strip()
        s = s.strip('\'"')
        return s
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

meta_df = meta_ds.to_dataframe()
meta_df = meta_df.map(clean_bytes_like_string)

profile_subset = prof_ds.isel(N_PROF=slice(0, 5))
rows = []
for prof_idx in range(profile_subset.dims["N_PROF"]):
    for level_idx in range(profile_subset.dims["N_LEVELS"]):
        row = {}
        for var in ["PLATFORM_NUMBER", "PROJECT_NAME", "PI_NAME", "DATA_CENTRE", 
                    "CYCLE_NUMBER", "JULD", "LATITUDE", "LONGITUDE"]:
            if var in profile_subset:
                val = profile_subset[var].values[prof_idx]
                if isinstance(val, (np.ndarray, list)):
                    val = val.item() if val.size == 1 else val.tolist()
                row[var.lower()] = val
        for var in ["PRES", "TEMP", "PSAL", "PRES_QC", "TEMP_QC", "PSAL_QC"]:
            if f"{var}_ADJUSTED" in profile_subset:
                row[var.lower()] = profile_subset[f"{var}_ADJUSTED"].values[prof_idx, level_idx]
            elif var in profile_subset:
                row[var.lower()] = profile_subset[var].values[prof_idx, level_idx]
            else:
                row[var.lower()] = None

        rows.append(row)
profile_df = pd.DataFrame(rows)
profile_df = profile_df.map(clean_bytes_like_string)
profile_df = profile_df.dropna(subset=["pres","temp","psal"], how="all")

trajectory_subset = traj_ds.isel(N_MEASUREMENT=slice(0, 1))
trajectory_df = trajectory_subset.to_dataframe().reset_index()
trajectory_df = trajectory_df.map(clean_bytes_like_string)
trajectory_df = trajectory_df[:300]

tech_df = tech_ds.to_dataframe()
tech_df = tech_df.map(clean_bytes_like_string)

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
    profile_df.to_sql("argo_profile", engine, if_exists="replace", index=False)

print("DataFrames successfully loaded into PostgreSQL tables.")

if __name__ == "__main__":
    main()
