import json
import psycopg2
from psycopg2.extras import execute_batch, execute_values
from datetime import datetime
import os
from dotenv import load_dotenv

# Add this function to help with timestamp parsing
def safe_timestamp_parse(timestamp_str):
    """Safely parse various timestamp formats"""
    if timestamp_str is None:
        return None

    # Common timestamp formats to try
    formats = [
        '%Y-%m-%d',
        '%d.%m.%Y',
        '%m/%d/%Y',
        '%d-%b-%Y',
        '%Y-%m-%d %H:%M:%S',  # 2025-07-15 16:26:00
        '%Y-%m-%d %H:%M:%S.%f',  # 2025-07-15 16:26:00.123
        '%d.%m.%Y %H:%M:%S',  # 15.07.2025 16:26:00
        '%Y/%m/%d %H:%M:%S',  # 2025/07/15 16:26:00
        '%m/%d/%Y %H:%M:%S',  # 07/15/2025 16:26:00
    ]

    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue

    print(f"Warning: Could not parse timestamp: {timestamp_str}")
    return None
class PostgresDrillingDb():

    logger = None
    connection = None

    def __init__(self, db_name : str,
                       db_user : str,
                       db_password : str,
                       db_host : str,
                       db_port : str):
        self.connection = psycopg2.connect(
                            dbname=db_name,
                            user=db_user,
                            password=db_password,
                            host=db_host,
                            port=db_port
                        )
        pass

    def set_logger(self, logger):
        self.logger = logger


    def close_connection(self):
        self.connection.commit()
        self.connection.close()
    # -----------------------------------
    # Private inserts
    # -----------------------------------
    def __insert_pile_metadata(self, json_data : dict):
        """
           Insert pile metadata data from json_data into PostgreSQL table pile_timeseries.
           :param json_data: dict parsed from the given JSON file
           :param connection: psycopg2 connection object
           """
        cursor = self.connection.cursor()
        success = False
        try:
            # --- Iterate through features ---
            for feature in json_data["features"]:
                props = feature["properties"]
                geom = feature.get("geometry", {})
                coords = geom.get("coordinates")
                # Build SQL insert statement (only properties, exclude "Data")
                insert_sql_string = """
                INSERT INTO pile_metadata
                ("JobNumber", "PileID", "Client", "Comments", "GeneralContractor",
                 "DelayReason", "DrillEndTime", "DrillNotes", "DrillStartTime", "Elevation",
                 "Filename", "GroutEndTime", "GroutStartTime", "HydraulicFlow", "JobName",
                 "Location", "LocationID", "MaxStroke", "Operator", "PileCode", "PileCutoff",
                 "PileDiameter", "PileLength", "PileStatus", "PowerPackID", "ProductCode",
                 "Project", "PumpCalibration", "PumpID", "InstallEndTime", "InstallStartTime",
                 "RigID", "StartDepth", "TargetPileLength", "TipElevation", "ToolOutTime",
                 "ToolWeight", "ToolID", "TurntableID", "TurntableWeight", "DrillTime",
                 "GroutTime", "GroutVolume", "InstallTime", "JobID", "OverBreak", "PileArea",
                 "PileVolume", "Area", "Drawing", "CageColor", "CapBeamType", "DesignJobNumber",
                 "DesignNotes", "DesignPileID", "PileCap", "PileType", "TopOfCage", "TopOfCap",
                 "XEasting", "YNorthing", "DelayTime", "MoveTime", "CycleTime", "MoveDistance",
                 "MoveVelocity", "UID", "Archived", "HasDesign", coordinates)
                VALUES (
                 %(JobNumber)s, %(PileID)s, %(Client)s, %(Comments)s, %(GeneralContractor)s,
                 %(DelayReason)s, %(DrillEndTime)s, %(DrillNotes)s, %(DrillStartTime)s, %(Elevation)s,
                 %(Filename)s, %(GroutEndTime)s, %(GroutStartTime)s, %(HydraulicFlow)s, %(JobName)s,
                 %(Location)s, %(LocationID)s, %(MaxStroke)s, %(Operator)s, %(PileCode)s, %(PileCutoff)s,
                 %(PileDiameter)s, %(PileLength)s, %(PileStatus)s, %(PowerPackID)s, %(ProductCode)s,
                 %(Project)s, %(PumpCalibration)s, %(PumpID)s, %(InstallEndTime)s, %(InstallStartTime)s,
                 %(RigID)s, %(StartDepth)s, %(TargetPileLength)s, %(TipElevation)s, %(ToolOutTime)s,
                 %(ToolWeight)s, %(ToolID)s, %(TurntableID)s, %(TurntableWeight)s, %(DrillTime)s,
                 %(GroutTime)s, %(GroutVolume)s, %(InstallTime)s, %(JobID)s, %(OverBreak)s, %(PileArea)s,
                 %(PileVolume)s, %(Area)s, %(Drawing)s, %(CageColor)s, %(CapBeamType)s, %(DesignJobNumber)s,
                 %(DesignNotes)s, %(DesignPileID)s, %(PileCap)s, %(PileType)s, %(TopOfCage)s, %(TopOfCap)s,
                 %(XEasting)s, %(YNorthing)s, %(DelayTime)s, %(MoveTime)s, %(CycleTime)s, %(MoveDistance)s,
                 %(MoveVelocity)s, %(UID)s, %(Archived)s, %(HasDesign)s,
                 ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)
                )
                ON CONFLICT ("JobNumber", "PileID") 
                DO UPDATE SET
                    "Client" = EXCLUDED."Client",
                    "Comments" = EXCLUDED."Comments",
                    "GeneralContractor" = EXCLUDED."GeneralContractor",
                    "DelayReason" = EXCLUDED."DelayReason",
                    "DrillEndTime" = EXCLUDED."DrillEndTime",
                    "DrillNotes" = EXCLUDED."DrillNotes",
                    "DrillStartTime" = EXCLUDED."DrillStartTime",
                    "Elevation" = EXCLUDED."Elevation",
                    "Filename" = EXCLUDED."Filename",
                    "GroutEndTime" = EXCLUDED."GroutEndTime",
                    "GroutStartTime" = EXCLUDED."GroutStartTime",
                    "HydraulicFlow" = EXCLUDED."HydraulicFlow",
                    "JobName" = EXCLUDED."JobName",
                    "Location" = EXCLUDED."Location",
                    "LocationID" = EXCLUDED."LocationID",
                    "MaxStroke" = EXCLUDED."MaxStroke",
                    "Operator" = EXCLUDED."Operator",
                    "PileCode" = EXCLUDED."PileCode",
                    "PileCutoff" = EXCLUDED."PileCutoff",
                    "PileDiameter" = EXCLUDED."PileDiameter",
                    "PileLength" = EXCLUDED."PileLength",
                    "PileStatus" = EXCLUDED."PileStatus",
                    "PowerPackID" = EXCLUDED."PowerPackID",
                    "ProductCode" = EXCLUDED."ProductCode",
                    "Project" = EXCLUDED."Project",
                    "PumpCalibration" = EXCLUDED."PumpCalibration",
                    "PumpID" = EXCLUDED."PumpID",
                    "InstallEndTime" = EXCLUDED."InstallEndTime",
                    "InstallStartTime" = EXCLUDED."InstallStartTime",
                    "RigID" = EXCLUDED."RigID",
                    "StartDepth" = EXCLUDED."StartDepth",
                    "TargetPileLength" = EXCLUDED."TargetPileLength",
                    "TipElevation" = EXCLUDED."TipElevation",
                    "ToolOutTime" = EXCLUDED."ToolOutTime",
                    "ToolWeight" = EXCLUDED."ToolWeight",
                    "ToolID" = EXCLUDED."ToolID",
                    "TurntableID" = EXCLUDED."TurntableID",
                    "TurntableWeight" = EXCLUDED."TurntableWeight",
                    "DrillTime" = EXCLUDED."DrillTime",
                    "GroutTime" = EXCLUDED."GroutTime",
                    "GroutVolume" = EXCLUDED."GroutVolume",
                    "InstallTime" = EXCLUDED."InstallTime",
                    "JobID" = EXCLUDED."JobID",
                    "OverBreak" = EXCLUDED."OverBreak",
                    "PileArea" = EXCLUDED."PileArea",
                    "PileVolume" = EXCLUDED."PileVolume",
                    "Area" = EXCLUDED."Area",
                    "Drawing" = EXCLUDED."Drawing",
                    "CageColor" = EXCLUDED."CageColor",
                    "CapBeamType" = EXCLUDED."CapBeamType",
                    "DesignJobNumber" = EXCLUDED."DesignJobNumber",
                    "DesignNotes" = EXCLUDED."DesignNotes",
                    "DesignPileID" = EXCLUDED."DesignPileID",
                    "PileCap" = EXCLUDED."PileCap",
                    "PileType" = EXCLUDED."PileType",
                    "TopOfCage" = EXCLUDED."TopOfCage",
                    "TopOfCap" = EXCLUDED."TopOfCap",
                    "XEasting" = EXCLUDED."XEasting",
                    "YNorthing" = EXCLUDED."YNorthing",
                    "DelayTime" = EXCLUDED."DelayTime",
                    "MoveTime" = EXCLUDED."MoveTime",
                    "CycleTime" = EXCLUDED."CycleTime",
                    "MoveDistance" = EXCLUDED."MoveDistance",
                    "MoveVelocity" = EXCLUDED."MoveVelocity",
                    "UID" = EXCLUDED."UID",
                    "Archived" = EXCLUDED."Archived",
                    "HasDesign" = EXCLUDED."HasDesign",
                    coordinates = EXCLUDED.coordinates;
                """

                # Coordinates: assuming GeoJSON [lon, lat]
                if coords and len(coords) >= 2:
                    props["lon"] = coords[0]
                    props["lat"] = coords[1]
                else:
                    props["lon"] = None
                    props["lat"] = None
                cursor.execute(insert_sql_string, props)
                # --- Commit and close ---
                self.connection.commit()
                log_msg = 'Ok processed pile metadata' + props["PileID"] + ' job id. ' + props["JobID"]
                success = True

        except psycopg2.Error as e:
            log_msg = 'Metadata insertion failed for ' + props["PileID"] + ' job id. ' + props["JobID"] + ': ' + str(e)
            print(f"Database error: {e}")
            self.connection.rollback()  # Always rollback on error
            # Retry logic or handle appropriately
        except Exception as e:
            log_msg = 'Metadata insertion failed for ' + props["PileID"] + ' job id. ' + props["JobID"] + ': ' + str(e)
        if self.logger is None:
            print(log_msg)
        else:
            # todo logger
            pass
        return success


    def __insert_pile_tseriesdata(self, json_data : dict):
        """
        Insert pile timeseries data from json_data into PostgreSQL table pile_timeseries.
        :param json_data: dict parsed from the given JSON file
        :param connection: psycopg2 connection object
        """
        features = json_data.get("features", [])
        if not features:
            return
        cursor = self.connection.cursor()
        success = False
        try:
            for feature in features:
                props = feature.get("properties", {})
                job_number = props.get("JobNumber")
                pile_id = props.get("PileID")
                data = props.get("Data", {})
                times = data.get("Time", [])
                # Prepare rows
                rows = []
                for i, t in enumerate(times):
                    parsed_time = safe_timestamp_parse(t)
                    rows.append((
                        job_number,
                        pile_id,
                        parsed_time,  # let PostgreSQL parse timestamp with TO_TIMESTAMP in query
                        data.get("Depth", [None]*len(times))[i],
                        data.get("PConcrete", [None]*len(times))[i],
                        data.get("RotaryHeadPressure", [None]*len(times))[i],
                        data.get("Rotation", [None]*len(times))[i],
                        data.get("PenetrationRate", [None]*len(times))[i],
                        data.get("Pulldown", [None]*len(times))[i],
                        data.get("Strokes", [None]*len(times))[i],
                        data.get("Torque", [None]*len(times))[i],
                        data.get("Easting", [None]*len(times))[i],
                        data.get("Northing", [None]*len(times))[i],
                        data.get("Elevation", [None]*len(times))[i],
                        data.get("DrillDirection", [None]*len(times))[i]
                    ))
                # SQL with timestamp conversion
                # was:  %s, %s, TO_TIMESTAMP(%s, 'DD.MM.YYYY HH24:MI:SS'),
                sql = """
                INSERT INTO pile_timeseries (
                    "JobNumber", "PileID", "Time",
                    "Depth", "PConcrete", "RotaryHeadPressure",
                    "Rotation", "PenetrationRate", "Pulldown", "Strokes", "Torque",
                    "Easting", "Northing", "Elevation", "DrillDirection"
                )
                VALUES (
                    %s, %s, %s::TIMESTAMP,
                    %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT ("JobNumber", "PileID", "Time") 
                DO UPDATE SET
                    "Depth" = EXCLUDED."Depth",
                    "PConcrete" = EXCLUDED."PConcrete",
                    "RotaryHeadPressure" = EXCLUDED."RotaryHeadPressure",
                    "Rotation" = EXCLUDED."Rotation",
                    "PenetrationRate" = EXCLUDED."PenetrationRate",
                    "Pulldown" = EXCLUDED."Pulldown",
                    "Strokes" = EXCLUDED."Strokes",
                    "Torque" = EXCLUDED."Torque",
                    "Easting" = EXCLUDED."Easting",
                    "Northing" = EXCLUDED."Northing",
                    "Elevation" = EXCLUDED."Elevation",
                    "DrillDirection" = EXCLUDED."DrillDirection";
                """

                # Batch insert for efficiency
                execute_batch(cursor, sql, rows, page_size=100)
            self.connection.commit()
            log_msg = 'Ok processed pile tseries' + props["PileID"] + ' job id. ' + props["JobID"]
            success = True
        except psycopg2.Error as e:
            log_msg = 'Tseries insertion failed for ' + props["PileID"] + ' job id. ' + props["JobID"] + ': ' + str(e)
            print(f"Database error: {e}")
            self.connection.rollback()  # Always rollback on error
        except Exception as e:
            log_msg = 'Tseries insertion failed for ' + props["PileID"] + ' job id. ' + props["JobID"] + ': ' + str(e)
        if self.logger is None:
            print(log_msg)
        else:
            # todo logger
            pass
        return success

    # -----------------------------------
    # Public inserts
    # -----------------------------------
    def insert_pile(self, json_data : dict):
        ok_metadata = self.__insert_pile_metadata(json_data)
        ok_tseries =  self.__insert_pile_tseriesdata(json_data)
        return ok_metadata, ok_tseries

    def insert_statistics(self, job_number: str, json_data: dict):
        """
        Inserts DailyStatistics and JobToDateStatistics into their respective tables
        from the provided JSON data. Updates existing records on conflict.
        """
        success = False
        try:
            with self.connection.cursor() as cursor:
                # Insert/Update DailyStatistics
                daily = json_data.get("DailyStatistics", {})
                if daily:
                    columns = ["Time", "RigID", "Piles", "sum_DrillTime", "mean_DrillTime",
                               "sum_InstallTime", "mean_InstallTime", "sum_DelayTime", "mean_DelayTime",
                               "sum_GroutTime", "mean_GroutTime", "TurnTime",
                               "sum_MoveTime", "mean_MoveTime", "sum_CycleTime", "mean_CycleTime",
                               "sum_PileLength", "mean_PileLength", "mean_OverBreak",
                               "sum_GroutVolume", "sum_PileVolume", "PileWaste",
                               "ConcreteDelivered", "LaborHours", "TurnStartTime",
                               "TurnEndTime", "ShiftStartTime", "ShiftEndTime", "ShiftTime", "RigWaste"]

                    # Debug: Check the data structure
                    print(f"Daily columns: {columns}")
                    print(f"Daily data keys: {list(daily.keys())}")

                    # Check if all columns exist in the data
                    for col in columns:
                        if col not in daily:
                            print(f"Warning: Column '{col}' not found in DailyStatistics data")

                    # Create values list safely
                    values = []
                    for i in range(len(daily.get("Time", []))):
                        row = [daily.get(col, [None])[i] if i < len(daily.get(col, [])) else None for col in columns]
                        values.append(row)

                    print(f"Number of daily rows: {len(values)}")

                    # prepend JobNumber to each row and remove duplicates
                    seen = set()
                    unique_values = []
                    for row in values:
                        if len(row) > 0:  # Ensure row has at least Time column
                            key = (job_number, row[0])  # (JobNumber, Time)
                            if key not in seen:
                                seen.add(key)
                                unique_values.append([job_number] + row)

                    print(f"Number of unique daily rows: {len(unique_values)}")

                    if unique_values:
                        all_columns = ["JobNumber"] + columns
                        cols_sql = ', '.join(f'"{c}"' for c in all_columns)
                        set_clause = ', '.join([f'"{col}" = EXCLUDED."{col}"' for col in columns])

                        print(f"Columns in SQL: {len(all_columns)}")
                        print(f"Sample row length: {len(unique_values[0])}")

                        sql = f'''
                        INSERT INTO daily_statistics ({cols_sql}) 
                        VALUES %s 
                        ON CONFLICT ("JobNumber", "Time") 
                        DO UPDATE SET {set_clause};
                        '''
                        execute_values(cursor, sql, unique_values)
                        print("Daily statistics inserted/updated successfully")

                # Insert/Update JobToDateStatistics
                job_to_date = json_data.get("JobToDateStatistics", {})
                if job_to_date:
                    columns = ["Time", "RigID", "PileCount","HoursMoved", "HoursDrilled",
                               "HoursGrouted", "HoursDelayed", "HoursTurn", "HoursCycle",
                               "DaysRigDrilled", "AveragePileLength", "AveragePileWaste",
                               "AverageRigWaste", "ConcreteDelivered", "LaborHours"]

                    # Debug: Check the data structure
                    print(f"ToDate columns: {columns}")
                    print(f"ToDate data keys: {list(job_to_date.keys())}")

                    # Check if all columns exist in the data
                    for col in columns:
                        if col not in job_to_date:
                            print(f"Warning: Column '{col}' not found in JobToDateStatistics data")

                    # Create values list safely
                    values = []
                    time_data = daily.get("Time", [])
                    for i in range(len(time_data)):
                        row = []
                        for col in columns:
                            if col == "Time" and i < len(time_data):
                                # Parse timestamp
                                time_str = time_data[i]
                                try:
                                    if isinstance(time_str, str):
                                        parsed_time = safe_timestamp_parse(time_str)
                                        # Handle ISO format "2025-07-15 16:26:00"
                                        # parsed_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                                    else:
                                        parsed_time = time_str
                                    row.append(parsed_time)
                                except ValueError as e:
                                    print(f"Error parsing timestamp {time_str}: {e}")
                                    row.append(None)
                            else:
                                # Other columns
                                col_data = daily.get(col, [])
                                row.append(col_data[i] if i < len(col_data) else None)
                        values.append(row)
                    # values = []
                    # for i in range(len(job_to_date.get("Time", []))):
                    #     row = [job_to_date.get(col, [None])[i] if i < len(job_to_date.get(col, [])) else None for col in
                    #            columns]
                    #     values.append(row)

                    print(f"Number of todate rows: {len(values)}")

                    # prepend JobNumber to each row and remove duplicates
                    seen = set()
                    unique_values = []
                    for row in values:
                        if len(row) > 0:  # Ensure row has at least Time column
                            key = (job_number, row[0])  # (JobNumber, Time)
                            if key not in seen:
                                seen.add(key)
                                unique_values.append([job_number] + row)

                    print(f"Number of unique todate rows: {len(unique_values)}")

                    if unique_values:
                        all_columns = ["JobNumber"] + columns
                        cols_sql = ', '.join(f'"{c}"' for c in all_columns)
                        set_clause = ', '.join([f'"{col}" = EXCLUDED."{col}"' for col in columns])

                        print(f"Columns in SQL: {len(all_columns)}")
                        print(f"Sample row length: {len(unique_values[0])}")

                        sql = f'''
                        INSERT INTO todate_statistics ({cols_sql}) 
                        VALUES %s 
                        ON CONFLICT ("JobNumber", "Time") 
                        DO UPDATE SET {set_clause};
                        '''
                        execute_values(cursor, sql, unique_values)
                        print("ToDate statistics inserted/updated successfully")

                self.connection.commit()
                log_msg = f'Ok processed statistics for {job_number}'
                success = True

        except Exception as e:
            log_msg = f'Failed to process statistics for {job_number}: {str(e)}'
            import traceback
            print(f"Full error: {traceback.format_exc()}")
            try:
                self.connection.rollback()
            except:
                pass

        if self.logger is None:
            print(log_msg)
        else:
            # todo logger
            pass
        return success



# _________________________________________________________________
# _________________________________________________________________
# _________________________________________________________________
# Examples
# _________________________________________________________________
# _________________________________________________________________
def test_example_insert_one_pile(loader : PostgresDrillingDb):
    '''
           Example of how to use the loader to insert a pile
    '''
    # --- Load JSON file ---
    with open("1632_2025_09_11_DR160_A139.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    ok_meta, ok_series = loader.insert_pile(data)
    print('metadata: ' + str(ok_meta))
    print('tseries: ' + str(ok_series))

def test_example_insert_statistics(loader : PostgresDrillingDb):
    # --- Load JSON file ---
    with open("1632_2025-09-25_Statistics.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    ok_stats = loader.insert_statistics('1632', data)
    print('statistics: ' + str(ok_stats))


if __name__ == "__main__":

    load_dotenv()
    database_psw = os.environ.get('DB_SECRET')
    database_host = os.environ.get('DB_HOST')
    test_insert_pile = False
    test_insert_statistics = True
    # --- Connection settings ---
    loader = PostgresDrillingDb(
                db_name="msdrilling",
                db_user="msdrilling_user",
                db_password=database_psw,
                db_host=database_host,
                db_port="5432")
