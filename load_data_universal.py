import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from get_data_from_PileMetrics_API import get_estimate
import naming_conventions as nc
import dash_leaflet as dl
from universal_loader import UniversalDataLoader,DataSource,PostgreSQLDataLoader
from dotenv import load_dotenv
load_dotenv()

assets_path = os.path.join(os.getcwd(), "assets")
geojson_folder = os.path.join(assets_path, 'data')
DATA_DIR = 'assets//pkl'
summary_folder = os.path.join(geojson_folder,'Summary')
color_map = {
    '3b82f6': 'blue', '0456fb': 'blue',
    'eab308': 'yellow', 'ffea00': 'yellow',
    '22c55e': 'green', 'ef4444': 'red',
    'f97316': 'orange', 'd946ef': 'purple',
    'None': 'brown'
}

columns_cpt = ['Depth (feet)','Elevation (feet)','q_c (tsf)','q_t (tsf)','f_s (tsf)','U_2 (ft-head)','U_0 (ft-head)','R_f (%)','Zone_Icn','SBT_Icn','B_q','F_r','Q_t','Ic','Q_tn','Q_s (Tons)','Q_b (Tons)','Q_ult (Tons)']
name_cpt_file_header = 'CPT-online-header.csv'
# # Create a dictionary to map Field to Group
groups_df = pd.read_csv(os.path.join(assets_path,'Groups.csv'))
groups_df = groups_df.explode("Group").reset_index(drop=True)
# Keep only relevant columns
filtered_columns = ["PileID", "Group", "Field", "Value", "latitude", "longitude", "date"]

def save_pickle(name, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    pd.to_pickle(data, _get_filepath(name))

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
def _get_filepath(job_number):
    return os.path.join(DATA_DIR, f"{job_number}.pkl")


def extract_coordinates_safe(point_str):
    """Safely extract longitude and latitude from POINT string"""
    if pd.isna(point_str) or point_str == '':
        return np.nan, np.nan

    try:
        # Check if it matches the expected format
        if not point_str.startswith('POINT(') or not point_str.endswith(')'):
            return np.nan, np.nan

        # Extract and convert coordinates
        coords = point_str.replace('POINT(', '').replace(')', '').split(',')
        if len(coords) == 2:
            return float(coords[0]), float(coords[1])
        elif len(coords)==1:
            coords = [float(x) for x in coords[0].split()]
            return coords[0],coords[1]
        else:
            return np.nan, np.nan
    except (ValueError, AttributeError):
        return np.nan, np.nan

# ====================================================================
load_dotenv()
database_psw = os.environ.get('DB_SECRET')
database_host = os.environ.get('DB_HOST')
postgres_loader = PostgreSQLDataLoader(
        host=database_host,
        database="msdrilling",
        user="msdrilling_user",
        password=database_psw,
        port="5432"
    )
# Create universal loader
universal_loader = UniversalDataLoader()
universal_loader.register_loader(DataSource.postgres, postgres_loader)

def load_data_from_db(jobs=[],reload:bool=False):
    result_MWD ={}
    results_CPT = {}
    results_pileMetrics ={}

    # jobid_pile_data = {}
    # jobid_cpt_data = {}
    # cpt_files_folder = 'CPT-files'
    # cpt_header = {}
    # cpt_data = {}

    for jobID in jobs:
        jobid_pile_data = {}
        jobid_cpt_data = {}
        cpt_files_folder = 'CPT-files'
        cpt_header = {}
        cpt_data = {}
        print(jobID)
        # =========================================================
        # Process Pile Design
        # =========================================================
        query_ts = """
        SELECT "JobNumber", "PileID", "Time", "Depth", "PConcrete", "RotaryHeadPressure", "Rotation", "PenetrationRate", "Pulldown", "Strokes", "Torque"
        FROM public.pile_timeseries
        WHERE "JobNumber" = %s
        AND (EXTRACT(SECOND FROM "Time")::integer %% 5 = 0)
        ORDER BY  "PileID","Time";
        """
        db_ts = postgres_loader.load_data_with_query(query=query_ts, params=(jobID,))
        db_ts = pd.DataFrame.from_dict(db_ts)

        query_ts_max = """SELECT 
            "PileID",
            ROUND(MAX("Strokes")::numeric, 0) as "MaxStroke",
            ROUND(MIN("Depth")::numeric, 0) as "MinDepth",
            MIN("Time") as "Time_Start"
        FROM public.pile_timeseries
        WHERE "JobNumber" = %s
        GROUP BY "PileID"
        ORDER BY "PileID";"""

        db_stroke_depth = postgres_loader.load_data_with_query(query=query_ts_max, params=(jobID,))
        db_stroke_depth = pd.DataFrame.from_dict(db_stroke_depth)

        query = """SELECT "JobNumber", "PileID", "Archived", "Area", "CageColor", "Client", "Comments", "CycleTime", "DelayReason", "DelayTime", "DesignJobNumber", "DesignNotes", "DesignPileID", "Drawing", "DrillEndTime", "DrillNotes", "DrillStartTime", "DrillTime", "Elevation", "Filename", "GeneralContractor", "GroutEndTime", "GroutStartTime", "GroutTime", "GroutVolume", "HasDesign", "HydraulicFlow", "InstallEndTime", "InstallStartTime", "InstallTime", "JobID", "JobName", "Location", "LocationID", "MaxStroke", "MoveDistance", "MoveTime", "MoveVelocity", "Operator", "OverBreak", "PileArea", "PileCap", "PileCode", "PileCutoff", "PileDiameter", "PileLength", "PileStatus", "PileType", "PileVolume", "PowerPackID", "ProductCode", "Project", "PumpCalibration", "PumpID", "RigID", "StartDepth", "TargetPileLength", "TipElevation", "ToolID", "ToolOutTime", "ToolWeight", "TopOfCage", "TopOfCap", "TurntableID", "TurntableWeight", "XEasting", "YNorthing", ST_AsText(coordinates) as coordinates
                                FROM public.pile_metadata   WHERE "JobNumber" = %s; """
        db_metadata = postgres_loader.load_data_with_query(query=query, params=(jobID,))
        db_metadata = pd.DataFrame.from_dict(db_metadata)
        if 'PileStatus' in db_metadata.columns:
            db_metadata = db_metadata[db_metadata['PileStatus'] == 'Complete']
        else:
            print('PileStatus not in cols for job:'+ str(jobID))

        query_stats = """SELECT * FROM public.daily_statistics  WHERE "JobNumber" = %s; """
        db_daily_stats = postgres_loader.load_data_with_query(query=query_stats, params=(jobID,))
        db_daily_stats = pd.DataFrame.from_dict(db_daily_stats)

        query_stats = """SELECT * FROM public.todate_statistics  WHERE "JobNumber" = %s; """
        db_todate_stats = postgres_loader.load_data_with_query(query=query_stats, params=(jobID,))
        db_todate_stats = pd.DataFrame.from_dict(db_todate_stats)

        stats_file = {'DailyStatistics':db_daily_stats,'JobToDateStatistics':db_todate_stats}

        df_design, estimates, location, markers_design = get_design(jobID,reload=reload)
        # df_design['latitude'] = df_design['latitude'].fillna(location['latitude'])
        # df_design['longitude'] = df_design['longitude'].fillna(location['longitude'])

        if len(db_metadata)>0:
            df = db_metadata.copy()
            df[['longitude', 'latitude']] = df['coordinates'].apply(
                lambda x: pd.Series(extract_coordinates_safe(x))
            )
            df['has_coord'] = df['latitude'].notna()
            df['latitude'] = df['latitude'].fillna(location.get('latitude'))
            df['longitude'] = df['longitude'].fillna(location.get('longitude'))

            time_columns = ['CycleTime', 'DelayTime', 'MoveTime','DrillTime',"InstallTime","GroutTime"]
            for col in time_columns:
                if col in df.columns:
                    df[col] = (df[col].fillna('0')
                        .astype(str)
                        .str.split(' ')
                        .str[0]
                        .astype(float)
                        .round(1)
                    )
            length_columns = ["MoveDistance","MoveVelocity",'PileLength']
            for col in length_columns:
                if col in df.columns:
                    df[col] = df[col].fillna(0) .astype(float).round(1)

            # 3. OverBreak - your specific transformation
            df['OverBreak'] = (
                    df['OverBreak']
                    .fillna(1)
                    .astype(float)
                    .sub(1)
                    .mul(100)
                    .clip(lower=0)
                    .round(0)
                    .astype(int)
                    .astype(str) + '%'
            )

            # 1. Filter out rows based on PileStatus and pile_id conditions
            # Original logic: Skip if PileStatus == 'Incomplete' AND pile_id doesn't start with RP, PB, or TP
            mask_to_remove = (
                    (df['PileStatus'] == 'Incomplete') &
                    (~df['PileID'].str.upper().str.startswith(('RP', 'PB', 'TP')))
            )

            # Print the piles being removed (optional)
            # incomplete_piles = df.loc[mask_to_remove, 'PileID']
            # if not incomplete_piles.empty:
            #     for pile_id in incomplete_piles:
            #         print(f'Pile: {pile_id} is incomplete.')

            # Remove these rows from the DataFrame
            df = df[~mask_to_remove].copy()

            # # 2. Handle PileType - convert to string and replace None/'nan' with 'None'
            # df['PileType'] = (
            #     df['PileType']
            #     .astype(str)
            #     .replace('None', 'None')  # This handles actual None values converted to string
            #     .replace('nan', 'None')  # This handles NaN values converted to string
            # )

            # Alternative more robust method for PileType:
            df['PileType'] = df['PileType'].apply(
                lambda x: 'None' if pd.isna(x) or str(x) == 'nan' else str(x)
            )

            # 3. Handle ProductCode - replace None/empty with 'DWP'
            df['ProductCode'] = df['ProductCode'].replace('', 'DWP').fillna('DWP')

            if estimates:  # This checks if dict is not empty
                df['colorCode'] = df['PileType'].apply(lambda x: estimates.get(x, {}).get('colorCode'))
            else:
                df['colorCode'] = None
            df.rename(columns={'MaxStroke':'MaxStrokeBase'},inplace=True)
            df = df.merge(db_stroke_depth,on='PileID',how='left')
            df['Time'] = df['Time_Start'].dt.strftime('%Y-%m-%d')
            df["date"] = df['Time_Start'].dt.strftime('%Y-%m-%d')
            df['color'] = df['colorCode'].map(color_map).fillna('blue')
            df['shape'] = df.apply(
                lambda row: get_shape_marker(row['PileCode'], row['PileStatus']),
                axis=1)

            # Merge the DataFrames on PileID
            db_ts_with_volume = db_ts.merge(
                df[['PileID', 'PumpCalibration']],
                on='PileID',
                how='left'
            )

            # Calculate the Volume column
            db_ts_with_volume['Volume'] = db_ts_with_volume['PumpCalibration'] * db_ts_with_volume['Strokes']

            jobid_pile_data[jobID] = db_ts_with_volume.copy()

            markers = {}
            for _, row in df.iterrows():
                markers[row['PileID']] = dl.Marker(
                    position=(row['latitude'], row['longitude']),
                    icon=dict(
                        iconUrl=f"/assets/icons/{row['color']}-{row['shape']}.png",
                        iconSize=[10, 10]
                    ),
                    children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row['PileStatus']}")]
                )

            # Melt the dataframe so each property is mapped to a Field and PileID
            melted_df = df.melt(id_vars=["PileID", "latitude", "longitude", "date"], var_name="Field",
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
            result_MWD[jobID] = (df, jobid_pile_data,merged_df,markers)
            results_CPT[jobID] = (cpt_header,jobid_cpt_data)
            results_pileMetrics[jobID] = (estimates,location,df_design,markers_design,stats_file)
            # result = (df, jobid_pile_data,merged_df,markers,cpt_header,jobid_cpt_data,estimates,location,df_design,markers_design,stats_file)
            #
            # save_pickle(jobID+'_db',result)

    return result_MWD,results_CPT,results_pileMetrics


def get_design(jobID,reload:bool=True):

    if reload:
        df_design = pd.DataFrame()
        estimates = None
        location = None
        markers_design = {}
        try:
            estimates, location, df_design = get_estimate(jobID)
            if len(df_design) > 0:
                col_keep = [nc.ds_pileid, nc.ds_status, nc.ds_lat, nc.ds_lon, nc.ds_productCode, nc.ds_piletype]
                # nc.ds_cage_color,nc.ds_date,nc.ds_rigid,
                df_design_merge = df_design[col_keep]
                df_design[nc.ds_pileid] = df_design[nc.ds_pileid].astype(str)
                df_design_merge['JobNumber'] = jobID
                df_design['color'] = df_design[nc.ds_cage_color].map(color_map).fillna('blue')
                df_design['latitude'] = df_design['latitude'].fillna(location['latitude'])
                df_design['longitude'] = df_design['longitude'].fillna(location['longitude'])
                # Create the dictionary markers_design
                for _, row in df_design.iterrows():
                    markers_design[row[nc.ds_pileid]] = dl.Marker(
                        position=(row[nc.ds_lat], row[nc.ds_lon]),
                        icon=dict(
                            iconUrl=f"/assets/icons/{row['color']}-donut.png",
                            iconSize=[10, 10]
                        ),
                        children=[dl.Tooltip(f"PileID: {row[nc.ds_pileid]}")]
                    )
                result = (df_design, estimates, location, markers_design)
                save_pickle(jobID + '_pilemetrics', result)
        except:
            pass
    else:
        cache_file = _get_filepath(jobID + '_pilemetrics')
        (df_design, estimates, location, markers_design) = pd.read_pickle(cache_file)

    return df_design, estimates, location, markers_design

if __name__ == '__main__':
    from datetime import datetime
    start = datetime.now()
    results = load_data_from_db(jobs=['1632','1639','1641','1642','1643','1648','1650','1652','1653','1655','1657','1660'],reload=False)
    print((datetime.now() - start).total_seconds()/60)