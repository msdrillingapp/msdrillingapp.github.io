import dropbox
import json
import pandas as pd
import naming_conventions as nc
import pickle
import os
from dotenv import load_dotenv
import os
load_dotenv()
APP_KEY = os.environ.get('DROPBOX_APP_KEY')
refresh_access_token = os.environ.get('DROPBOX_TOKEN')
database_psw = os.environ.get('DB_SECRET')
database_host = os.environ.get('DB_HOST')

dbx = dropbox.Dropbox(
        app_key=APP_KEY,
        oauth2_refresh_token=refresh_access_token
        # app_secret is optional here if you obtained the refresh token via PKCE
    )
# def list_folders(path):
#     """List subfolders and files under a path"""
#     entries = dbx.files_list_folder(path).entries
#     return entries

def list_folders(path):
    """List all entries (files + folders) under a path, handling pagination"""
    result = dbx.files_list_folder(path)
    entries = result.entries

    # Keep fetching while there are more entries
    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        entries.extend(result.entries)

    return entries

def read_json_files(base_folder="/JSON",jobs=[]):
    job_data = {}
    job_stats = {}

    # List all subfolders (job ids) under /JSON
    for entry in list_folders(base_folder):
        if isinstance(entry, dropbox.files.FolderMetadata):
            jobid = entry.name
            # if jobid in jobs:
            if True:
                job_folder = f"{base_folder}/{jobid}"
                job_data[jobid] = []
                job_stats[jobid] = []
                mdates= None
                # List all files in the job folder
                for subentry in list_folders(job_folder):
                    if isinstance(subentry, dropbox.files.FileMetadata) and subentry.name.endswith(".json"):
                        file_path = f"{job_folder}/{subentry.name}"
                        _, res = dbx.files_download(file_path)
                        content = res.content.decode("utf-8")
                        if subentry.name.endswith("Statistics.json"):
                            if subentry.name.split('_')[0] == jobid:
                                fdate = subentry.name.split('_')[1]
                                try:
                                    fdate = pd.to_datetime(fdate).date()
                                    if mdates is None:
                                        mdates = fdate
                                    else:
                                        if fdate<mdates:
                                            continue
                                except:
                                    pass
                                try:
                                    job_stats[jobid]=json.loads(content)
                                except json.JSONDecodeError:
                                    print(f"⚠️ Could not decode {file_path}")

                        else:
                            try:
                                job_data[jobid].append(json.loads(content))
                            except json.JSONDecodeError:
                                print(f"⚠️ Could not decode {file_path}")

    return job_data,job_stats


def read_json_files_recent(base_folder="/JSON", jobs=[], days_threshold=5):
    job_data = {}
    job_stats = {}

    # Calculate the cutoff date
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=days_threshold)

    # List all subfolders (job ids) under /JSON
    for entry in list_folders(base_folder):
        if isinstance(entry, dropbox.files.FolderMetadata):
            jobid = entry.name
            if True:
            # if jobid in jobs:
                job_folder = f"{base_folder}/{jobid}"
                job_data[jobid] = []
                job_stats[jobid] = []
                mdates = None

                # List all files in the job folder
                for subentry in list_folders(job_folder):
                    if isinstance(subentry, dropbox.files.FileMetadata) and subentry.name.endswith(".json"):

                        # Check if file was modified within the threshold
                        file_modified = subentry.client_modified
                        if file_modified.replace(tzinfo=None) < cutoff_date:
                            continue  # Skip files older than threshold

                        file_path = f"{job_folder}/{subentry.name}"
                        _, res = dbx.files_download(file_path)
                        content = res.content.decode("utf-8")

                        if subentry.name.endswith("Statistics.json"):
                            if subentry.name.split('_')[0] == jobid:
                                fdate = subentry.name.split('_')[1]
                                try:
                                    fdate = pd.to_datetime(fdate).date()
                                    if mdates is None:
                                        mdates = fdate
                                    else:
                                        if fdate < mdates:
                                            continue
                                except:
                                    pass
                                try:
                                    job_stats[jobid] = json.loads(content)
                                except json.JSONDecodeError:
                                    print(f"⚠️ Could not decode {file_path}")
                        else:
                            try:
                                job_data[jobid].append(json.loads(content))
                            except json.JSONDecodeError:
                                print(f"⚠️ Could not decode {file_path}")

    return job_data, job_stats




def write_data(filename, data):
    try:
        with open(filename, 'wb') as file:
            pickle.dump(data, file)
        print(f"Data successfully written to {filename}")
    except Exception as e:
        print(f"Error writing file: {e}")

# Reading data
def read_data(filename):
    try:
        with open(filename, 'rb') as file:  # Note 'rb' for reading
            return pickle.load(file)
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

if __name__ == '__main__':
    assets_path = os.path.join(os.getcwd(), "assets")
    dropbox_pkl_dir = os.path.join(assets_path,'dropbox_pkl')
    dbx = dropbox.Dropbox(
        app_key=APP_KEY,
        oauth2_refresh_token=refresh_access_token
        # app_secret is optional here if you obtained the refresh token via PKCE
    )

    from db_loader.msdrilling_db_load import PostgresDrillingDb


    # jobs = nc.ALL_AVAILABLE_JOBS
    jobs = ['1639','1648','1632',  '1641', '1642', '1643','1648', '1650', '1652', '1653',
                          '1655','1657', '1660']
    reload = True
    load_recent = True
    if reload:
        if load_recent:
            drilling_data,stats_data = read_json_files_recent(base_folder='/JSON',jobs=jobs,days_threshold=3)
            fname_drilling = os.path.join(dropbox_pkl_dir,'drilling_data_recent.pkl')
            write_data(fname_drilling,drilling_data)
            fname_stats = os.path.join(dropbox_pkl_dir, 'stats_data_recent.pkl')
            write_data(fname_stats, stats_data)
        else:
            drilling_data, stats_data = read_json_files(base_folder='/JSON', jobs=jobs)
            fname_drilling = os.path.join(dropbox_pkl_dir, 'drilling_data.pkl')
            write_data(fname_drilling, drilling_data)
            fname_stats = os.path.join(dropbox_pkl_dir, 'stats_data.pkl')
            write_data(fname_stats, stats_data)
    else:
        drilling_data = read_data(os.path.join(dropbox_pkl_dir,'drilling_data_recent.pkl'))
        stats_data = read_data(os.path.join(dropbox_pkl_dir,'stats_data_recent.pkl'))
        # drilling_data = read_data(os.path.join(dropbox_pkl_dir, 'drilling_data.pkl'))
        # stats_data = read_data(os.path.join(dropbox_pkl_dir, 'stats_data.pkl'))
    # jobs=['1648']
    for jobID in jobs:
        loader = PostgresDrillingDb(
            db_name="msdrilling",
            db_user="msdrilling_user",
            db_password=database_psw,
            db_host=database_host,
            db_port="5432")
        try:
            if len((drilling_data[jobID]))>0:
                for data in drilling_data[jobID]:
                    ok_meta, ok_series = loader.insert_pile(data)
            if len(stats_data[jobID])>0:
                ok_stats = loader.insert_statistics(jobID, stats_data[jobID])
            loader.connection.close()
        except:
            print('Error job: '+ str(jobID))
            continue

    loader.connection.close()

