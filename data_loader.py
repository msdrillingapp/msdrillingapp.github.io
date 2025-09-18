import pandas as pd
import os
from Job import JobManager
from get_data_from_PileMetrics_API import get_estimate
from cache_manager import ChartDataCache
import naming_conventions as nc
import json
import dash_leaflet as dl
from datetime import datetime
# from database.DatabaseStorage import Databasestorage
# from flask_login import current_user

# Precompute once and reuse
color_map = {
    '3b82f6': 'blue', '0456fb': 'blue',
    'eab308': 'yellow', 'ffea00': 'yellow',
    '22c55e': 'green', 'ef4444': 'red',
    'f97316': 'orange', 'd946ef': 'purple',
    'None': 'brown'
}
# Simple singleton implementation
class DataManager:
    _instance = None
    _data = None
    _is_loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataManager, cls).__new__(cls)
        return cls._instance

    def load_data(self,jobs,reload:bool=False):
        """Load data if not already loaded"""
        if not self._is_loaded:
            print("Loading data for the first time...")
            try:
                # Call your data loading function
                result_MWD, results_CPT,results_pileMetrics = load_geojson_data(jobs, reload=reload)
                my_jobs = JobManager()
                for jobID, v in results_pileMetrics.items():
                    my_job = my_jobs.add_job(v[1])
                    my_job.add_estimates(v[0])
                    my_job.add_pile_schedule(v[2])
                    my_job.add_colorCodes(v[0])
                    my_job.add_design_markers(v[3])
                    my_job.add_stats_files(v[4])

                cache_manager = ChartDataCache(result_MWD, reload=reload)

                self._data = {
                    'result_MWD': result_MWD,
                    'results_CPT': results_CPT,
                    'my_jobs': my_jobs,
                    'cache_manager': cache_manager
                }

                self._is_loaded = True
                print(f"Data loaded successfully: {len(result_MWD)} jobs")
            except Exception as e:
                print(f"Error : {e}")
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


def load_all_data(jobs):
    """Load data (forces load if not loaded)"""
    return data_manager.load_data(jobs)


def get_data():
    """Get data without forcing load"""
    return data_manager.get_data()

# from dash import  html
current_user = None
def ensure_data_loaded():
    if not current_user == None:
        if not current_user.is_authenticated:
            jobs = nc.ALL_AVAILABLE_JOBS
            # return html.Div("Please login to access this page", style={'color': 'white', 'padding': '20px'})

        jobs = current_user.get_accessible_jobs()
    else:
        jobs = nc.ALL_AVAILABLE_JOBS
    """Ensure data is loaded, then return it"""
    return data_manager.load_data(jobs)


def get_job_data(job_id):
    data = ensure_data_loaded([job_id])
    return data['result_MWD'].get(job_id, None)


# def get_all_job_ids():
#     data = ensure_data_loaded()
#     return list(data['result_MWD'].keys())

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
summary_folder = os.path.join(geojson_folder,'Summary')

def _get_filepath(job_number):
    return os.path.join(DATA_DIR, f"{job_number}.pkl")


# Convert data types to match table schema

def prepare_dataframe_for_db(df,type_conversions):
    """
    Prepare DataFrame to match the database table schema
    """
    # Create a copy to avoid modifying original
    df_prepared = df.copy()
    for col, dtype in type_conversions.items():
        if col in df_prepared.columns:
            try:
                if 'datetime' in dtype:
                    df_prepared[col] = pd.to_datetime(df_prepared[col], errors='coerce')
                elif 'float' in dtype:
                    df_prepared[col] = pd.to_numeric(df_prepared[col], errors='coerce')
                elif 'int' in dtype:
                    df_prepared[col] = pd.to_numeric(df_prepared[col], errors='coerce').astype('Int64')
                elif 'str' in dtype:
                    df_prepared[col] = df_prepared[col].astype(str)
            except Exception as e:
                print(f"Warning: Could not convert column {col} to {dtype}: {e}")
                df_prepared[col] = None
    # Rename columns to match table schema
    df_prepared.columns = [col.lower() for col in df_prepared.columns]

    return df_prepared
# ========================================================================
def load_geojson_data(jobs=[],reload:bool=False):
    result_MWD ={}
    results_CPT = {}
    results_pileMetrics ={}

    # config_file = os.path.join(os.getcwd(),'database','database.ini')
    # data_storage = Databasestorage()
    # data_storage.configure_from_config(config_file)

    for jobID in jobs:
        print(jobID)
        get_data = True
        if not reload:
            cache_file = _get_filepath(jobID)
            if os.path.exists(cache_file):
                (properties_df, jobid_pile_data,merged_df,markers,cpt_header, jobid_cpt_data,estimates,location,df_design,markers_design,stats_file) = pd.read_pickle(cache_file)
                result_MWD[jobID] = (properties_df, jobid_pile_data,merged_df,markers)
                results_CPT[jobID] = (cpt_header, jobid_cpt_data)
                results_pileMetrics[jobID] = (estimates,location,df_design,markers_design,stats_file)
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
            markers = {}
            markers_design = {}
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
                    df_design['color'] = df_design[nc.ds_cage_color].map(color_map).fillna('blue')
                    # Create the dictionary
                    markers_design = {}
                    for _, row in df_design.iterrows():
                        markers_design[row[nc.ds_pileid]] = dl.Marker(
                            position=(row[nc.ds_lat], row[nc.ds_lon]),
                            icon=dict(
                                iconUrl=f"/assets/icons/{row['color']}-donut.png",
                                iconSize=[10, 10]
                            ),
                            children=[dl.Tooltip(f"PileID: {row[nc.ds_pileid]}")]
                        )
            except :
                pass
            # =========================================================
            # Read stats file
            # =========================================================
            stats_files = os.listdir(summary_folder)
            stats_file = {}
            try:
                for f in stats_files:
                    if f.startswith(jobID) and f.endswith("Statistics.json"):
                        file_path = os.path.join(summary_folder, f)
                        with open(file_path, "r", encoding="utf-8") as f:
                            stats_file = json.load(f)
                            break
            except:
                print('Warning! No stats file was found')
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
                        print(pile_id)
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
                        DelayTime = properties["DelayTime"] if not properties["DelayTime"] is None else 0
                        properties["DelayTime"] = round(float(str(DelayTime).split(' ')[0]),1)
                        MoveTime = properties["MoveTime"] if not properties["MoveTime"] is None else 0
                        properties["MoveTime"] = round(float(str(MoveTime).split(' ')[0]),1)
                        DrillTime = properties["DrillTime"] if not properties["DrillTime"] is None else 0
                        properties["DrillTime"] = round(float(str(DrillTime).split(' ')[0]),1)
                        InstallTime = properties["InstallTime"] if not properties["InstallTime"] is None else 0
                        properties["InstallTime"] = round(float(str(InstallTime).split(' ')[0]),1)
                        GroutTime = properties["GroutTime"] if not properties["GroutTime"] is None else 0
                        properties["GroutTime"] = round(float(str(GroutTime).split(' ')[0]),1)
                        MoveDistance = properties.get("MoveDistance",0)  if not properties.get("MoveDistance",0)  is None else 0
                        properties["MoveDistance"] = round(float(MoveDistance),1)
                        MoveVelocity = properties.get("MoveVelocity", 0) if not properties.get("MoveVelocity",                                                                   0) is None else 0
                        properties["MoveVelocity"] = round(float(MoveVelocity), 1)
                        properties['PileLength'] = round(float(properties.get('PileLength',0)), 1)
                        # properties['PumpCalibration'] = round(float(properties.get('PumpCalibration', 2)), 1)
                        # ================================================
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
                            if jobID=='1650':
                                properties['ProductCode'] = 'DeWaal Pile'
                            else:
                                properties['ProductCode'] = 'DWP'



                        pile_id = properties['PileID']
                        if len(estimates) > 0:
                            try:
                                colorCode  = estimates[properties['PileType']]['colorCode']
                            except:
                                colorCode = None
                        else:
                            colorCode = None
                        properties['colorCode'] = colorCode

                        job_id = properties.get("JobNumber")
                        if str(job_id)!=jobID:
                            print('Error '+str(job_id))
                            pileid_list_wrong.append(pile_id)
                            properties['JobNumber'] = jobID

                        calibration = properties["PumpCalibration"]
                        strokes = properties["Data"].get("Strokes", [])
                        depths = properties["Data"].get("Depth", [])
                        time_start = properties["Data"].get("Time", [])
                        time_start = pd.to_datetime(time_start[0],format='%d.%m.%Y %H:%M:%S')

                        date = time_start.date().strftime(format='%Y-%m-%d')

                        properties['Time'] = date
                        properties["date"] = date  # Store the date from the filename

                        properties['MaxStroke'] = max(strokes)
                        properties['MinDepth'] = round(min(depths),1)
                        properties['Time_Start'] = time_start

                        if float(properties['PileDiameter']) > 3:
                            print('For PileID:' + pile_id + ' diameter is  ' + str(properties['PileDiameter']))

                        volume = [calibration*float(x) for x in strokes]
                        data_names= list(properties['Data'].keys())
                        if 'PenetrationRate' not in data_names:
                            if 'Speed' in data_names:
                                properties['Data']['PenetrationRate'] = properties['Data']['Speed']
                        if 'Pulldown' not in data_names:
                            if 'WinchLoad' in data_names:
                                properties['Data']['Pulldown'] = properties['Data']['WinchLoad']
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
            # data2send = prepare_dataframe_for_db(pile_data,nc.type_conversions_DrillingRecords)
            # data_storage.write_to_storage(data2send)
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

                properties_df['color'] = properties_df['colorCode'].map(color_map).fillna('blue')
                properties_df['shape'] = properties_df.apply(lambda row: get_shape_marker(row['PileCode'], row['PileStatus']),
                                                       axis=1)
                markers = {}
                for _, row in properties_df.iterrows():
                    markers[row['PileID']] = dl.Marker(
                        position=(row['latitude'], row['longitude']),
                        icon=dict(
                            iconUrl=f"/assets/icons/{row['color']}-{row['shape']}.png",
                            iconSize=[10, 10]
                        ),
                        children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row['PileStatus']}")]
                    )

                # Melt the dataframe so each property is mapped to a Field and PileID
                melted_df = properties_df.melt(id_vars=["PileID", "latitude", "longitude", "date"], var_name="Field",
                                               value_name="Value")
                # Convert non-string values to strings to avoid DataTable errors
                melted_df["Value"] = melted_df["Value"].astype(str)
                # Merge with Groups.csv
                merged_df = melted_df.merge(groups_df, on="Field", how="left")
                merged_df["Group"].fillna("Undefined", inplace=True)  # Ensure Group is always a string
                merged_df = merged_df[filtered_columns]
            # ========================================================
            # data2send = prepare_dataframe_for_db(properties_df,nc.type_conversions_DrillingRecords)
            # data_storage.write_to_storage(data2send)
            # ========================================================
            result_MWD[jobID] = (properties_df, jobid_pile_data,merged_df,markers)
            results_CPT[jobID] = (cpt_header,jobid_cpt_data)
            results_pileMetrics[jobID] = (estimates,location,df_design,markers_design,stats_file)
            result = (properties_df, jobid_pile_data,merged_df,markers,cpt_header,jobid_cpt_data,estimates,location,df_design,markers_design,stats_file)

            save_pickle(jobID,result)

    return result_MWD,results_CPT,results_pileMetrics


def save_pickle(job_number, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    pd.to_pickle(data, _get_filepath(job_number))

def get_color_marker(coloCode):
    if coloCode in ['3b82f6','0456fb']:
        return 'blue'
    elif coloCode in ['eab308','ffea00']:
        return 'yellow'
    elif coloCode=='22c55e' :
        return 'green'
    elif coloCode == 'ef4444':
        return 'red'
    elif coloCode == 'f97316':
        return 'orange'
    elif coloCode == 'd946ef':
        return 'purple'
    elif coloCode =='None':
        return 'brown'
    else:
        return 'blue' #'grey'

def get_shape_marker(pile_code,pile_status):
    if pile_code.lower() == "Production Pile".lower():  # Circle
        shape='donut'
    elif pile_code.lower() == "TEST PILE".lower():  # Square
        shape = 'square'
    elif pile_code.lower() == "REACTION PILE".lower():  # Octagon
        shape = 'target'
    else:
        shape ='triangle'
    if pile_status == 'Complete':
        shape += '_fill'

    return shape


# Add this function to data_loader.py
def get_user_specific_jobs(user_permissions, all_available_jobs):
    """
    Return jobs that the user has access to
    """
    if 'all' in user_permissions:
        return all_available_jobs
    else:
        # Return intersection of user permissions and available jobs
        return [job for job in user_permissions if job in all_available_jobs]

if __name__ == "__main__":
    data_manager = DataManager()
    jobs = nc.ALL_AVAILABLE_JOBS
    data_manager.load_data(jobs=jobs,reload=True)




