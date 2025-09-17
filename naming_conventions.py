
# PileCode": "PP",  "PileCode": "PRODUCTION PILE",
# "PileCode": "TP",  "PileCode": "TEST PILE",
# "PileCode": "RP", "PileCode": "REACTION PILE",
# "PileCode": "PB", "PileCode": "PROBE",
pile_status = ["Complete", "Abandoned","Not Started"]
# base coordinates
# baseCoordinates_file ='Summary/BaseCoordinates.csv'
# design output table
# designOutput_file = '-DesignOutput.csv'
# ds_pileid = 'DesignPileID'
# ds_status = 'HasBeenDrilled'
# ds_date = 'DrillDate'
# ds_rigid = 'RigID'
# ds_cage_color = 'CageColor'
# ds_lat = 'Latitude'
# ds_lon = 'Longitude'
# ds_pilecode = 'PileCode'
# ds_piletype = 'PileType'
# ds_east = 'XEasting'
# ds_north = 'YNorthing'
#=====================================================
ds_pileid = 'pileId'
ds_status = 'pileStatus'
ds_lat = 'latitude'
ds_lon = 'longitude'
ds_piletype = 'type'
ds_east = 'easting'
ds_north = 'northing'
ds_productCode = 'productCode'
ds_cage_color = 'color_rrggbb'


# job estimate file
job_estimate_file = '-ESTIMATE-SHEET.csv'
estimate_count ='COUNT'
estimate_man_hours = 'MAN HOURS'
estimate_rig_days = 'RIG DAYS'

# site progression
job_site_progression_file = '-SiteProgression.xlsx'
site_prog_daily_tab = 'DAILY'
site_prog_to_date_tab = 'Job To Date'

# database Piles
pile_id = 'PileID'

type_conversions_DrillingRecords = {
        'JobNumber': 'int64',
        'PileID': 'str',
        'JobName': 'str',
        'Date': 'datetime64[ns]',
        'RigID': 'str',
        'LocationID': 'str',
        'PileCode': 'str',
        'PileStatus': 'str',
        'PileType': 'str',
        'ProductCode': 'str',
        'PileDiameter': 'float64',
        'PileLength': 'float64',
        'Latitude': 'float64',
        'Longitude': 'float64',
        'MinDepth': 'float64',
        'MaxStroke': 'float64',
        'Time_Start': 'datetime64[ns]',
        'Comments': 'str',
        'DelayReason': 'str',
        'DrillStartTime': 'datetime64[ns]',
        'DrillEndTime': 'datetime64[ns]',
        'DrillNotes': 'str',
        'Elevation': 'float64',
        'GroutStartTime': 'datetime64[ns]',
        'GroutEndTime': 'datetime64[ns]',
        'Operator': 'str',
        'PumpCalibration': 'float64',
        'PumpID': 'str',
        'InstallStartTime': 'datetime64[ns]',
        'InstallEndTime': 'datetime64[ns]',
        'GroutVolume': 'float64',
        'PileArea': 'float64',
        'PileVolume': 'float64',
        'Area': 'float64',
        'DesignJobNumber': 'float64',
        'DesignNotes': 'str',
        'DesignPileID': 'str',
        'XEasting': 'float64',
        'YNorthing': 'float64',
        'InstallTime': 'float64',
        'OverBreak': 'float64',
        'DrillTime': 'float64',
        'GroutTime': 'float64',
        'DelayTime': 'float64',
        'MoveTime': 'float64',
        'CycleTime': 'float64',
        'MoveDistance': 'float64',
        'MoveVelocity': 'float64'
    }

type_conversions_DrillingTimeSeries = {
        'JobNumber': 'int64',
        'PileID': 'str',
        'Time': 'datetime64[ns]',
        'Strokes': 'float64',
        'Depth': 'float64',
        'RotaryHeadPressure': 'float64',
        'Rotation': 'float64',
        'PenetrationRate': 'float64',
        'Pulldown': 'float64',
        'Torque': 'float64',
        'Volume': 'float64'}




