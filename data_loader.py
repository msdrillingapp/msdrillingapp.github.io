import pandas as pd
import os
from Job import JobManager
from get_data_from_PileMetrics_API import get_estimate
from cache_manager import ChartDataCache
import naming_conventions as nc
import json
from datetime import datetime


# Simple singleton implementation
class DataManager:
    _instance = None
    _data = None
    _is_loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataManager, cls).__new__(cls)
        return cls._instance

    def load_data(self,reload:bool=False):
        """Load data if not already loaded"""
        if not self._is_loaded:
            print("Loading data for the first time...")
            try:
                ALL_JOBS =['1640', '1633', '1642','1650'] #, '1648',,'1640', '1633', '1642','1641','1604',
                # Call your data loading function
                result_MWD, results_CPT,results_pileMetrics = load_geojson_data(ALL_JOBS, reload=reload)
                my_jobs = JobManager()
                for jobID, v in results_pileMetrics.items():
                    my_job = my_jobs.add_job(v[1])
                    my_job.add_estimates(v[0])
                    my_job.add_pile_schedule(v[2])
                    my_job.add_colorCodes(v[0])

                cache_manager = ChartDataCache(result_MWD)

                self._data = {
                    'result_MWD': result_MWD,
                    'results_CPT': results_CPT,
                    'my_jobs': my_jobs,
                    'cache_manager': cache_manager
                }

                self._is_loaded = True
                print(f"Data loaded successfully: {len(result_MWD)} jobs")
            except Exception as e:
                print(f"Error loading data for job:{jobID} error: {e}")
                self._data = {'result_MWD': {}, 'results_CPT': {}, 'my_jobs': None,'cache_manager':None}
                self._is_loaded = True
        return self._data

    def get_data(self):
        """Get data - returns empty dict if not loaded yet"""
        if self._is_loaded:
            return self._data
        else:
            return  {'result_MWD': {}, 'results_CPT': {}, 'my_jobs': None,'cache_manager':None}


# Create global instance
data_manager = DataManager()


def set_cache(cache_instance):
    # For compatibility, not used
    pass


def load_all_data():
    """Load data (forces load if not loaded)"""
    return data_manager.load_data()


def get_data():
    """Get data without forcing load"""
    return data_manager.get_data()


def ensure_data_loaded():
    """Ensure data is loaded, then return it"""
    return data_manager.load_data()


def get_job_data(job_id):
    data = ensure_data_loaded()
    return data['result_MWD'].get(job_id, None)


def get_all_job_ids():
    data = ensure_data_loaded()
    return list(data['result_MWD'].keys())

# ====================================================================================
assets_path = os.path.join(os.getcwd(), "assets")
geojson_folder = os.path.join(assets_path, 'data')

columns_cpt = ['Depth (feet)','Elevation (feet)','q_c (tsf)','q_t (tsf)','f_s (tsf)','U_2 (ft-head)','U_0 (ft-head)','R_f (%)','Zone_Icn','SBT_Icn','B_q','F_r','Q_t','Ic','Q_tn','Q_s (Tons)','Q_b (Tons)','Q_ult (Tons)']
name_cpt_file_header = 'CPT-online-header.csv'
# Keep only relevant columns
filtered_columns = ["PileID", "Group", "Field", "Value", "latitude", "longitude", "date"]

# # Create a dictionary to map Field to Group
groups_df = pd.read_csv(os.path.join(assets_path,'Groups.csv'))
groups_df = groups_df.explode("Group").reset_index(drop=True)
# ========================================================================
DATA_DIR = 'assets//pkl'

def _get_filepath(job_number):
    return os.path.join(DATA_DIR, f"{job_number}.pkl")
# ========================================================================
def load_geojson_data(jobs=[],reload:bool=False):
    result_MWD ={}
    results_CPT = {}
    results_pileMetrics ={}

    for jobID in jobs:
        get_data = True
        if not reload:
            cache_file = _get_filepath(jobID)
            if os.path.exists(cache_file):
                (properties_df, jobid_pile_data,merged_df,cpt_header, jobid_cpt_data,estimates,location,df_design) = pd.read_pickle(cache_file)
                result_MWD[jobID] = (properties_df, jobid_pile_data,merged_df)
                results_CPT[jobID] = (cpt_header, jobid_cpt_data)
                results_pileMetrics[jobID] = (estimates,location,df_design)
                print('Loaded pickle data for jobNumber: '+ jobID)
                get_data = False

        if get_data:
            pileid_list_wrong = []
            all_data = []
            jobid_pile_data ={}
            jobid_cpt_data = {}
            cpt_files_folder = 'CPT-files'
            cpt_header = {}
            pile_data = {}
            cpt_data = {}
            data_folder = os.path.join(geojson_folder,jobID)
            merged_df = pd.DataFrame()
            # =========================================================
            # Process Pile Design
            # =========================================================
            df_design = None
            try:
                estimates, location, df_design = get_estimate(jobID)
                if len(df_design)>0:
                    col_keep = [nc.ds_pileid,nc.ds_status,nc.ds_lat,nc.ds_lon,nc.ds_productCode,nc.ds_piletype]
                    # nc.ds_cage_color,nc.ds_date,nc.ds_rigid,
                    df_design_merge = df_design[col_keep]
                    df_design[nc.ds_pileid] = df_design[nc.ds_pileid].astype(str)
                    df_design_merge['JobNumber'] = jobID
            except :
                pass
            # =========================================================
            # Process CPT data
            # =========================================================
            dir_cpt_data = os.path.join(data_folder, cpt_files_folder)
            if os.path.exists(dir_cpt_data):
                if os.path.isfile(os.path.join(dir_cpt_data, name_cpt_file_header)):
                    headers = pd.read_csv(os.path.join(dir_cpt_data, name_cpt_file_header))
                    # 994-402_1_cpt.mat
                    headers['Name'] = headers['File Name'].str.split('_cpt.mat').str[0]
                    cpt_header[jobID] = headers
                    for cpt_file in os.listdir(dir_cpt_data):
                        if cpt_file == name_cpt_file_header:
                            continue
                        cpt_data_file = pd.read_csv(os.path.join(dir_cpt_data,cpt_file))
                        holeid = cpt_data_file['HoleID'].values[0] # CPT-1
                        for c in columns_cpt:
                            if holeid in cpt_data:
                                cpt_data[holeid].update({c: list(cpt_data_file[c].values)})
                            else:
                                cpt_data[holeid] = {c: list(cpt_data_file[c].values)}
                    jobid_cpt_data[jobID] = cpt_data
            # ===================================================
            # End Process CPT data
            # =========================================================
            for filename in os.listdir(data_folder):
                if filename.endswith(".json"):
                    file_path = os.path.join(data_folder, filename)

                    with open(file_path, "r", encoding="utf-8") as f:
                        geojson_data = json.load(f)

                    features = geojson_data.get("features", [])

                    for feature in features:
                        properties = feature.get("properties", {})
                        geometry = feature.get("geometry", {})
                        coords = geometry.get("coordinates", [])
                        pile_id = properties['PileID']
                        lon = None
                        lat = None
                        if coords and len(coords) >= 2:
                            lon, lat = coords[:2]  # Ensure correct coordinate order

                        if lon is None:
                            if pile_id.upper().endswith('RD'):
                                pile_id = pile_id.upper().split('RD')[0]
                            if len(df_design)>0:
                                if pile_id in df_design[nc.ds_pileid].values:
                                    lat = df_design[df_design[nc.ds_pileid]==pile_id][nc.ds_lat].values[0]
                                    lon = df_design[df_design[nc.ds_pileid]==pile_id][nc.ds_lon].values[0]
                            if lon is None:
                                lat = float(location['latitude'])
                                lon = float(location['longitude'])

                        properties["latitude"] = lat
                        properties["longitude"] = lon
                        # ================================================
                        # Remove the pile from the design piles list to avoid duplicates
                        # if len(piles_list)>0:
                        #     if pile_id in piles_list:
                        #         piles_list.remove(pile_id)
                        # ================================================
                        #  do not include incomplete piles
                        pileStatus = properties.get("PileStatus")
                        if (pileStatus =='Incomplete') and not (pile_id.upper().startswith('RP') or pile_id.upper().startswith('PB') or pile_id.upper().startswith('TP')):
                            print('Pile: ' + pile_id +' is incomplete.')
                            continue
                        properties['PileType'] = str(properties['PileType'])
                        if (properties['PileType'] is None) or (properties['PileType']=='nan') :
                            properties['PileType'] = 'None'

                        if (properties['ProductCode'] is None) or (properties['ProductCode']==''):
                            properties['ProductCode'] = 'DWP'


                        pile_id = properties['PileID']
                        job_id = properties.get("JobNumber")
                        if str(job_id)!=jobID:
                            print('Error '+str(job_id))
                            pileid_list_wrong.append(pile_id)
                            properties['JobNumber'] = jobID

                        calibration = float(properties.get("PumpCalibration"))
                        strokes = properties["Data"].get("Strokes", [])
                        depths = properties["Data"].get("Depth", [])
                        time_start = properties["Data"].get("Time", [])
                        time_start = pd.to_datetime(time_start[0],format='%d.%m.%Y %H:%M:%S')

                        date = time_start.date().strftime(format='%Y-%m-%d')

                        properties['Time'] = date
                        properties["date"] = date  # Store the date from the filename

                        properties['MaxStroke'] = max(strokes)
                        properties['MinDepth'] = min(depths)
                        properties['Time_Start'] = time_start

                        if float(properties['PileDiameter']) > 3:
                            print('For PileID:' + pile_id + ' diameter is  ' + str(properties['PileDiameter']))

                        volume = [calibration*float(x) for x in strokes]
                        if pile_id and "Data" in properties:
                            time = properties["Data"].get("Time", [])
                            pile_data[pile_id] = {properties['date']: {
                                "Time": properties["Data"].get("Time", []),
                                "Strokes": properties["Data"].get("Strokes", [0]*len(time)),
                                "Depth": properties["Data"].get("Depth", [0]*len(time)),
                                'RotaryHeadPressure': properties['Data'].get('RotaryHeadPressure', [0]*len(time)),
                                'Rotation': properties['Data'].get('Rotation', [0]*len(time)),
                                'PenetrationRate': properties['Data'].get('PenetrationRate', [0]*len(time)),
                                'Pulldown': properties['Data'].get('Pulldown', [0]*len(time)),
                                'Torque': properties['Data'].get('Torque', [0]*len(time)),
                                'Volume': volume}}

                        all_data.append(properties)
            jobid_pile_data[jobID] = pile_data.copy()
            # Cache the result for next time
            properties_df = pd.DataFrame(all_data)
            if len(properties_df)>0:
                properties_df['PileType'] = properties_df['PileType'].apply(lambda x: 'None' if x == '' or str(x).lower() == 'nan' else x)
                if 'FileName' in properties_df.columns:
                    properties_df.drop(columns=['FileName'], inplace=True)
                if 'Data' in properties_df.columns:
                    properties_df.drop(columns=['Data'], inplace=True)
                if 'UID' in properties_df.columns:
                    properties_df.drop(columns=['UID'], inplace=True)

                properties_df['Time'].fillna(datetime.today())
                properties_df['JobNumber'] = properties_df['JobNumber'].astype(str)

                # Melt the dataframe so each property is mapped to a Field and PileID
                melted_df = properties_df.melt(id_vars=["PileID", "latitude", "longitude", "date"], var_name="Field",
                                               value_name="Value")
                # Convert non-string values to strings to avoid DataTable errors
                melted_df["Value"] = melted_df["Value"].astype(str)
                # Merge with Groups.csv
                merged_df = melted_df.merge(groups_df, on="Field", how="left")
                merged_df["Group"].fillna("Undefined", inplace=True)  # Ensure Group is always a string
                merged_df = merged_df[filtered_columns]

            result_MWD[jobID] = (properties_df, jobid_pile_data,merged_df)
            results_CPT[jobID] = (cpt_header,jobid_cpt_data)
            results_pileMetrics[jobID] = (estimates,location,df_design)
            result = (properties_df, jobid_pile_data,merged_df,cpt_header,jobid_cpt_data,estimates,location,df_design)

            save_pickle(jobID,result)

    return result_MWD,results_CPT,results_pileMetrics


def save_pickle(job_number, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    pd.to_pickle(data, _get_filepath(job_number))



if __name__ == "__main__":
    data_manager = DataManager()
    data_manager.load_data(reload=True)




