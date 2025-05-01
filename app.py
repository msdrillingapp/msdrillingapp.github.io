import dash
import pandas as pd
import os
from datetime import datetime
import numpy as np

from dash.exceptions import PreventUpdate
import dash_leaflet as dl
from dash import no_update

from dash import dcc, html, Output, Input, State,ClientsideFunction,DiskcacheManager, CeleryManager
from flask_caching import Cache
import plotly.graph_objects as go
import dash_auth
import dash_bootstrap_components as dbc
from flask import Flask
# from tasks import celery_app
import functions as ts
from celery.result import AsyncResult
from layouts import get_filters,get_pilelist,get_pile_details_cards,get_header,get_filtered_table,add_charts


#############################################################################
# Keep this out of source code repository - save in a file or a database
VALID_USERNAME_PASSWORD_PAIRS = {
    'Dennis': 'Meara'
}
# REDIS_URL = "redis://red-d05pmaa4d50c73f9cnsg:6379"

if '__file__' in globals():
    root_path = os.path.dirname(os.path.abspath(__file__))
else:
    # Fallback for environments where __file__ isn't available
    root_path = os.getcwd()

# Create required directories if they don't exist
os.makedirs(os.path.join(root_path, "cache"), exist_ok=True)
os.makedirs(os.path.join(root_path, "instance"), exist_ok=True)
# if 'REDIS_URL' in os.environ:
if 'REDIS_URL' in os.environ:
    # Use Redis & Celery if REDIS_URL set as an env variable
    # from celery_config import celery_app
    # from celery import Celery
    # celery_app = Celery(__name__, broker=os.environ['REDIS_URL'], backend=os.environ['REDIS_URL'])
    # celery_app.conf.update(
    #     task_serializer='json',
    #     result_serializer='json',
    #     accept_content=['json']
    # )
    from celery_worker import celery
    background_callback_manager = CeleryManager(celery)
else:
    # Diskcache for non-production apps when developing locally
    import diskcache
    # Configure diskcache for background callbacks
    cache = diskcache.Cache(os.path.join(root_path, "cache"))
    background_callback_manager = DiskcacheManager(cache)
# ======================================================
# Folder containing GeoJSON files
file_path = os.path.join(os.getcwd(), "assets",)
geojson_folder = os.path.join(file_path,'data')
#############################################################################

def create_app(server):

    # server = Flask(
    #     __name__,
    #     instance_path=os.path.join(root_path, 'instance'),
    #     root_path=root_path,
    #     static_folder=os.path.join(root_path, 'assets')
    # )
    # # Create Dash app background_callback_manager=background_callback_manager,server=server,
    app = dash.Dash(__name__, server=server,
                    assets_folder=os.path.join(root_path, 'assets'),
                    external_stylesheets=["/assets/style.css", dbc.themes.BOOTSTRAP],
                    suppress_callback_exceptions=True,
                    background_callback_manager=background_callback_manager,
                    meta_tags=[{'name': 'viewport',
                                'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.2, minimum-scale=0.5,'}]
                    )

    app.title = 'MS Drill Tracker'

    # Initialize caching right here
    # cache = Cache(app.server, config={
    #     'CACHE_TYPE':'FileSystemCache' ,  # Or 'RedisCache' for better performance if available
    #     'CACHE_DIR': 'cache-directory',   # Directory for cache files
    #     'CACHE_THRESHOLD': 1000,          # Max number of items
    #     'CACHE_DEFAULT_TIMEOUT': 86400    # Cache expires after 1 day (in seconds)
    # })

    # cache.clear()
    # Clear cache for a specific memoized function
    # cache.delete_memoized(load_geojson_data)
    # Make sure this directory exists
    # os.makedirs('cache-directory', exist_ok=True)

    #####################
    # # Create a dictionary to map Field to Group
    groups_df = pd.read_csv(os.path.join(file_path,'Groups.csv'))
    groups_df = groups_df.explode("Group").reset_index(drop=True)

    # Load all datasets
    (properties_df, pile_data,latitudes,longitudes,markers,jobid_pile_data) = ts.load_geojson_data()

    properties_df.drop(columns=['Data','UID','FileName'],inplace=True)

    # Melt the dataframe so each property is mapped to a Field and PileID
    melted_df = properties_df.melt(id_vars=["PileID","latitude", "longitude", "date"], var_name="Field", value_name="Value")
    # Convert non-string values to strings to avoid DataTable errors
    melted_df["Value"] = melted_df["Value"].astype(str)
    # Merge with Groups.csv
    merged_df = melted_df.merge(groups_df, on="Field", how="left")
    merged_df["Group"].fillna("Undefined", inplace=True)  # Ensure Group is always a string
    # Keep only relevant columns
    filtered_columns = ["PileID", "Group", "Field", "Value", "latitude", "longitude", "date"]
    merged_df = merged_df[filtered_columns]
    groups_list = list(merged_df["Group"].dropna().unique())
    groups_list.remove('Edit')
    # groups_list.insert(0, 'Edit')

    # Track changed values
    changed_values ={}

    # Calculate map center and zoom
    if latitudes and longitudes:
        # lat = [float(item) for var in latitudes for item in latitudes if item != 'None']
        center_lat = np.nanmean([float(item) for var in latitudes for item in latitudes if not item is None])
        center_lon = np.nanmean([float(item) for var in longitudes for item in longitudes if not item is None])
        map_center = [center_lat, center_lon]
        zoom_level = 8  # Adjust zoom for a closer view
    else:
        map_center = [40, -100]
        zoom_level = 4


    # auth = dash_auth.BasicAuth(
    #     app,
    #     VALID_USERNAME_PASSWORD_PAIRS
    # )
    flts = get_filters(properties_df)
    pilelist = get_pilelist()
    header = get_header()
    charts = add_charts()
    filtered_table = get_filtered_table()
    app.layout = html.Div([
        # ============================================================
        dcc.Store(id='window-size', data={'width': 1200}),
        header,
        html.Br(),
        # FILTERS ===================================================================
        flts,
        # ===============================================
        html.Div([
            # Statistics Info Cards
            html.Div(id="pile-summary-cards-jobid", style={
                'display': 'flex', 'justifyContent': 'space-around', 'alignItems': 'center',
                'backgroundColor': '#193153', 'color': 'white', 'padding': '10px',
                'borderRadius': '5px', 'marginTop': '5px'
            }),
        ]),
        # =====================================================================================
        # MAP==================================================================================
        # =====================================================================================
        html.Div([
            # Map Section
            dbc.Button("Show Map", id="toggle-map", color="primary", className="mb-2",style={"backgroundColor": "#f7b500", "color": "black",  "border": "2px solid #f7b500"}),
            dbc.Collapse(
                dl.Map(id="map", center=map_center, zoom=zoom_level, zoomControl=True, children=[
                    dl.TileLayer(
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",  # Default OSM tiles
                        maxZoom=19,  # Higher max zoom (OSM supports up to 19)
                        minZoom=2,  # Lower min zoom (adjust as needed)
                    ),
                    dl.LayerGroup(markers, id="map-markers"),

                ], style={
                        'width': '100%',
                        'height': '400px',
                        'margin': '0 auto',  # Better centering
                    },),

                id="collapse-map",
                is_open=True
            ),
        ]),
        # ======================================================
        html.Br(),
        # =====================================================================================
        pilelist,
        # ======================================================
        # Table & Chart Side by Side
        html.Div([
            # Plots Section
            dbc.Button("Show Plots", id="toggle-plots", color="primary", className="mb-2", style={"marginTop": "20px"}),
            charts,
        # =======================================================================
        # Views Section (Main Table)
        dbc.Button("Show Table", id="toggle-views", color="primary", className="mb-2", style={"marginTop": "20px"}),

        dbc.Collapse(
            html.Div([
                dbc.Row([
                    dbc.Col(
                        html.Div([
                                html.Label("Filter by Group:", style={'color': 'white'}),
                                dcc.Dropdown(
                                    id="group-filter",
                                    options=[{"label": g, "value": g} for g in groups_list],
                                    placeholder="Filter by Group",
                                    value='Edit',
                                    style={'marginBottom': '20px', 'marginRight': '10px'},
                                    className="dark-dropdown"
                                ),]),
                        xs=10, sm=5, md=8, lg=3, xl=3  # Move these properties outside as well
                    )
                ]),
                filtered_table,
                html.Br(),
                ]),
                id="collapse-views",
                is_open=False
            )

        ]),
        # ===============================================================================================
        # Scroll to Top Button
        html.Button("⬆ Scroll to Top", id="scroll-top-button", n_clicks=0, style={
            'position': 'fixed', 'bottom': '20px', 'right': '20px', 'zIndex': '1000',
            'padding': '10px 15px', 'fontSize': '16px', 'cursor': 'pointer',
            'backgroundColor': '#1f4068', 'color': 'white', 'border': 'none',
            'borderRadius': '5px'
        })

    ], style={'backgroundColor': '#193153', 'height': '550vh', 'padding': '20px', 'position': 'relative'})

    # ================================================================================================
    # ================================================================================================
    # ================================================================================================
    app.clientside_callback(
        ClientsideFunction(namespace="clientside", function_name="scrollToTop"),
        Output("scroll-top-button", "n_clicks"),
        Input("scroll-top-button", "n_clicks")
    )
    # Callback to filter table
    @app.callback(
        # Output("filtered-table", "data"),
        Output("filtered-table", "rowData"),
        # [Input("pileid-filter", "value"),
        #  Input("date-filter", "value"),
        [ Input('pilelist-table', 'selectedRows'),
         Input("group-filter", "value")],prevent_initial_call=True,
    )
    def update_table(selected_row, selected_group):
        if not selected_row:
            return []  # Return an empty table before selection
        filtered_df = merged_df.copy()

        selected_row = selected_row[0]  # Get first selected row (since we're using single selection)
        selected_pileid = selected_row['PileID']
        selected_date = pd.to_datetime(selected_row['Time']).date().strftime(format='%Y-%m-%d')
        # Filter DataFrame based on selected PileID and Date
        filtered_df = filtered_df[(filtered_df["PileID"] == selected_pileid) & (filtered_df["date"] == selected_date)]

        if not selected_group is None:
            filtered_df = filtered_df[filtered_df["Group"] == selected_group]

        # if selected_group == "Edit":
        #     # Reorder fields based on custom_order, keeping other fields at the end
        #     sorted_fields = sorted(filtered_df["Field"].unique(), key=lambda x: custom_order.index(x) if x in custom_order else len(custom_order))
        #     filtered_df = filtered_df.set_index("Field").loc[sorted_fields].reset_index()
        #     # tmp = pd.DataFrame([selected_pileid,selected_group,'PileID',selected_pileid,1,1,selected_date],columns=filtered_df.columns)
        #     new_row = ['PileID',selected_pileid,selected_group,selected_pileid,filtered_df.loc[1,'latitude'],filtered_df.loc[1,'longitude'],selected_date]
        #     filtered_df = pd.concat([pd.DataFrame([new_row], columns=filtered_df.columns), filtered_df]).reset_index(drop=True)
        #     # Add "Edited Value" column
        #     # filtered_df["Original Value"] = filtered_df["Value"]
        #     filtered_df["Edited Value"] = filtered_df["Value"]  # User edits this column
        #     out = filtered_df[["Field", "Value", "Edited Value"]].to_dict("records")
        #     out_dict = {item['Field']: item['Value'] for item in out}

            # # Modify OverBreak if it exists
            # if 'OverBreak' in out_dict:
            #     out_dict['OverBreak'] = f"{float(out_dict['OverBreak']) * 100:.2f}%"
            #
            # # Convert back to list of dictionaries
            # out = [{'Field': k, 'Value': v,'Edited Value':v} for k, v in out_dict.items()]
            # return out
        # else:
        out = filtered_df[["Field", "Value"]].to_dict("records")
        out_dict = {item['Field']: item['Value'] for item in out}

        # Modify OverBreak if it exists
        if 'OverBreak' in out_dict:
            overbreak = float(out_dict['OverBreak'])
            overbreak = overbreak* 100-100.0
            out_dict['OverBreak'] = f"{overbreak :.0f}%"
        if 'MoveDistance' in out_dict:
            movetime = round(float(out_dict['MoveDistance']),1)
            out_dict['MoveDistance'] = movetime
        if 'PileArea' in out_dict:
            movetime = round(float(out_dict['PileArea']),1)
            out_dict['PileArea'] = movetime
        if 'PileVolume' in out_dict:
            movetime = round(float(out_dict['PileVolume']),1)
            out_dict['PileVolume'] = movetime
        if 'GroutVolume' in out_dict:
            movetime = round(float(out_dict['GroutVolume']), 1)
            out_dict['GroutVolume'] = movetime

        # Convert back to list of dictionaries
        out = [{'Field': k, 'Value': v} for k, v in out_dict.items()]

        return out

    @app.callback(
        Output("pilelist-table", "rowData"),
        [Input("jobid-filter", "value"),
         Input("date-filter", "value"),
        Input("rigid-filter", "value")
         ],prevent_initial_call=True,
    )
    def update_table(selected_jobid, selected_date,selected_rigid):
        if not selected_jobid and not selected_date:
            return []  # Return an empty table before selection
        filtered_df = properties_df.copy()
        # Filter DataFrame based on selected PileID and Date
        if not selected_jobid is None:
            filtered_df = filtered_df[(filtered_df["JobID"] == selected_jobid)]
        if not selected_date is None:
            filtered_df = filtered_df[(filtered_df["date"] == selected_date)]
        if not selected_rigid is None:
            filtered_df = filtered_df[(filtered_df["RigID"] == selected_rigid)]

        summary_data = []
        for _, row in filtered_df.iterrows():
            pile_id = row["PileID"]

            time = row['Time']
            try:
                time = pd.to_datetime(time)
            except:
                pass
            movetime = row['MoveTime']
            try:
                movetime = datetime.strptime(movetime, '%H:%M:%S').time()
            except:
                pass
            totaltime = row['TotalTime']
            try:
                totaltime = datetime.strptime(totaltime, '%H:%M:%S').time()
            except:
                pass
            delaytime = row['DelayTime']
            try:
                delaytime = datetime.strptime(delaytime, '%H:%M:%S').time()
            except:
                pass
            movedistance = row['MoveDistance']
            try:
                movedistance = round(float(movedistance),1)
            except:
                pass

            if not selected_date is None:
                use_date = selected_date
            else:
                use_date = time.date().strftime(format='%Y-%m-%d')
            # Retrieve Depth & Strokes from pile_data
            if pile_id in pile_data and use_date in pile_data[pile_id]:
                depth_values = pile_data[pile_id][use_date]["Depth"]
                strokes_values = pile_data[pile_id][use_date]["Strokes"]
                min_depth = min(depth_values) if depth_values else None
                max_strokes = max(strokes_values) if strokes_values else None
            else:
                min_depth = None
                max_strokes = None

            # try:
            #     pile_id = int(pile_id)
            # except:
            #     pass

            dict_data = {

                "PileID": pile_id,
                "Time": time,
                "JobID": row['JobID'],
                "LocationID": row['LocationID'],
                "MinDepth": min_depth,
                "MaxStrokes": max_strokes,
                "OverBreak": f"{(row['OverBreak'] - 1) * 100:.0f}%",
                "PileStatus": row['PileStatus'],
                "PileCode": row['PileCode'],
                "Comments": row["Comments"],
                "DelayTime": delaytime,
                "Delay": row['Delay'],
                "PumpID": row['PumpID'],
                "Calibration": row['PumpCalibration'],
                "PileType": row['PileType'],
                "Distance" : movedistance,
                "MoveTime": movetime,
                "Totaltime": totaltime,
                "RigID":row['RigID'],
                "Client":row['Client'],
                "DrillStartTime": row['DrillStartTime'],
                "DrillEndTime": row['DrillEndTime'],
                "PileLength": row['PileLength'],
                "PileDiameter": row['PileDiameter'],


            }
            summary_data.append(dict_data)

        return summary_data


    # =================================================================================================
    # Callback to update dropdown options based on selections
    @app.callback(
        [
            Output("date-filter", "options"),
            Output("rigid-filter", "options"),
            Output("pileid-filter", "options"),
            # Output("pileid-filter-top", "options"),
            Output("pilecode-filter", "options"),
            Output("pilestatus-filter", "options"),
            Output("piletype-filter", "options"),
            Output("productcode-filter", "options"),

            Output("date-filter", "value"),
            Output("rigid-filter", "value"),
            Output("pileid-filter", "value"),
            # Output("pileid-filter-top", "value"),
            Output("pilecode-filter", "value"),
            Output("pilestatus-filter", "value"),
            Output("piletype-filter", "value"),
            Output("productcode-filter", "value"),
            # Output("group-filer","value")
        ],
        [
            Input("jobid-filter", "value"),
            Input("date-filter", "value"),
            Input("rigid-filter", "value"),
            Input("pileid-filter", "value"),
            # Input("pileid-filter-top", "value"),
            Input("pilecode-filter", "value"),
            Input("pilestatus-filter", "value"),
            Input("piletype-filter", "value"),
            Input("productcode-filter", "value"),
        ],
        [
            State("date-filter", "value"),
            State("rigid-filter", "value"),
            State("pileid-filter", "value"),
            # State("pileid-filter-top", "value"),
            State("pilecode-filter", "value"),
            State("pilestatus-filter", "value"),
            State("piletype-filter", "value"),
            State("productcode-filter", "value"),
        ], allow_duplicate=True,prevent_initial_call=True,
    )
    def update_filter_options(selected_jobid, selected_date, selected_rigid, selected_pileid,
                              selected_pilecode, selected_pilestatus, selected_piletype, selected_productcode,
                              prev_date, prev_rigid, prev_pileid,  prev_pilecode, prev_pilestatus, prev_piletype,
                              prev_productcode):
        ctx = dash.callback_context  # Get the trigger
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

        # Start with full dataset
        filtered_df = properties_df.copy()

        # Apply filtering based on selected values
        if selected_jobid:
            filtered_df = filtered_df[filtered_df["JobID"] == selected_jobid]
        if selected_date:
            filtered_df = filtered_df[filtered_df["date"] == selected_date]
        if selected_rigid:
            filtered_df = filtered_df[filtered_df["RigID"] == selected_rigid]
        # if selected_pileid or selected_pileid_top:  # Sync both PileID filters
        #     selected_pileid = selected_pileid or selected_pileid_top
        #     filtered_df = filtered_df[filtered_df["PileID"] == selected_pileid]
        if selected_pilecode:
            filtered_df = filtered_df[filtered_df["PileCode"] == selected_pilecode]
        if selected_pilestatus:
            filtered_df = filtered_df[filtered_df["PileStatus"] == selected_pilestatus]
        if selected_piletype:
            filtered_df = filtered_df[filtered_df["PileType"] == selected_piletype]
        if selected_productcode:
            filtered_df = filtered_df[filtered_df["ProductCode"] == selected_productcode]

        # Generate new options based on filtered data
        out = list(filtered_df["date"].dropna().unique())
        out = [pd.to_datetime(x).date() for x in out]
        out.sort()
        out = [x.strftime(format='%Y-%m-%d') for x in out]
        date_options = [{"label": d, "value": d} for d in out]
        rigid_options = [{"label": r, "value": r} for r in filtered_df["RigID"].unique()]
        pileid_options = [{"label": p, "value": p} for p in filtered_df["PileID"].unique()]
        pilecode_options = [{"label": p, "value": p} for p in filtered_df["PileCode"].unique()]
        pilestatus_options = [{"label": p, "value": p} for p in filtered_df["PileStatus"].unique()]
        piletype_options = [{"label": p, "value": p} for p in filtered_df["PileType"].unique()]
        productcode_options = [{"label": p, "value": p} for p in filtered_df["ProductCode"].unique()]


        # Reset values **ONLY IF JobID was changed**
        if triggered_id == "jobid-filter":
            return (date_options, rigid_options, pileid_options,  pilecode_options, pilestatus_options,
                    piletype_options, productcode_options,
                    None, None, None, None,  None, None, None)  # Reset everything

        # Sync pileid-filter and pileid-filter-top
        if triggered_id == "pileid-filter":
            return (date_options, rigid_options, pileid_options,  pilecode_options, pilestatus_options,
                    piletype_options, productcode_options,
                    prev_date, prev_rigid, selected_pileid,  prev_pilecode, prev_pilestatus, prev_piletype,
                    prev_productcode)

        # if triggered_id == "pileid-filter-top":
        #     return (date_options, rigid_options, pileid_options, pileid_options, pilecode_options, pilestatus_options,
        #             piletype_options, productcode_options,
        #             prev_date, prev_rigid, selected_pileid_top, selected_pileid_top, prev_pilecode, prev_pilestatus,
        #             prev_piletype, prev_productcode)

        # Otherwise, **keep previous selections**
        return (date_options, rigid_options, pileid_options, pilecode_options, pilestatus_options, piletype_options,
                productcode_options,
                prev_date, prev_rigid, prev_pileid,  prev_pilecode, prev_pilestatus, prev_piletype, prev_productcode)




    # ==================================================================================================
    # Callback to update map markers and recenter the map
    @app.callback(
        [Output("map-markers", "children"),
         Output("map", "center"),
         Output('map','zoom'),
         Output("map", "key")],
        [dash.dependencies.Input("date-filter", "value"),
         dash.dependencies.Input("rigid-filter", "value"),
         dash.dependencies.Input("pileid-filter", "value"),
         dash.dependencies.Input('jobid-filter', "value"),
         dash.dependencies.Input('pilecode-filter', "value"),
         dash.dependencies.Input('pilestatus-filter', "value"),
         dash.dependencies.Input('piletype-filter', "value"),
         dash.dependencies.Input('productcode-filter', "value")
         ],prevent_initial_call=True
    )
    def update_map_markers(selected_date, selected_rigid, selected_pileid,selected_jobid,selected_pilecode,selected_pilestatus,selected_piletype,selected_productcode):
        filtered_df = properties_df.copy()

        center = [np.nanmean(list(ts.filter_none(properties_df["latitude"]))), np.nanmean(list(ts.filter_none(properties_df["longitude"])))]
        zoom_level = 8
        # Apply filters
        if not selected_date is None:
            filtered_df = filtered_df[filtered_df["date"] == selected_date]
        if not selected_rigid is None:
            filtered_df = filtered_df[filtered_df["RigID"] == selected_rigid]
            zoom_level = 20
        if not selected_pileid is None:
            filtered_df = filtered_df[filtered_df["PileID"] == selected_pileid]
            zoom_level = 45
        if not selected_jobid is None:
            filtered_df = filtered_df[filtered_df['JobID'] == selected_jobid]
            zoom_level = 20
        if not selected_pilecode is None:
            filtered_df = filtered_df[filtered_df['PileCode'] == selected_pilecode]
        if not selected_pilestatus is None:
            filtered_df = filtered_df[filtered_df['PileStatus'] == selected_pilestatus]
        if not selected_piletype is None:
            filtered_df = filtered_df[filtered_df['PileType'] == selected_piletype]
        if not selected_productcode is None:
            filtered_df = filtered_df[filtered_df['ProductCode'] == selected_productcode]

        markers = []
        if len(filtered_df)>0:

            center = [np.nanmean(list(ts.filter_none(filtered_df["latitude"]))), np.nanmean(list(ts.filter_none(filtered_df["longitude"])))]  # Default center

            for _, row in filtered_df.iterrows():
                if pd.notna(row["latitude"]) and pd.notna(row["longitude"]):
                    pile_code = row.get("PileCode", "")
                    piletype = row.get("PileType", "")
                    if piletype=='1':
                        use_color = '#327ba8'
                    elif piletype=='2':
                        use_color = 'yellow'
                    elif piletype=='3':
                        use_color = 'green'
                    elif piletype=='3A':
                        use_color='purple'
                    elif piletype=='4':
                        use_color='red'
                    elif piletype=='5':
                        use_color='orange'
                    else:
                        use_color='black'

                    # Assign different marker styles
                    if pile_code.lower() == "Production Pile".lower():  # Circle
                        marker = dl.CircleMarker(
                            center=(row["latitude"], row["longitude"]),
                            radius=5, color=use_color, fill=True,
                            fillColor=use_color,  # Set fill color (can be same as stroke)
                            fillOpacity=1.0,  # Make sure it's fully opaque
                            children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")]
                        )

                    elif pile_code.lower() == "TEST PILE".lower():  # Square (Using a rectangle as an approximation)
                        marker = dl.Rectangle(
                            bounds=[(row["latitude"] - 0.0001, row["longitude"] - 0.0001),
                                    (row["latitude"] + 0.0001, row["longitude"] + 0.0001)],
                            color=use_color, fill=True,fillOpacity=1.0,
                            children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")]
                        )

                    elif pile_code.lower() == "REACTION PILE".lower():  # Octagon (Using a custom SVG marker)
                        marker = dl.Marker(
                            position=(row["latitude"], row["longitude"]),
                            icon={
                                # "iconUrl": "https://upload.wikimedia.org/wikipedia/commons/4/4f/Octagon_icon.svg",
                                "iconUrl":  "https://en.wikipedia.org/wiki/Triangle#/media/File:Triangle_illustration.svg",
                                "iconSize": [20, 20]  # Adjust size
                            },
                            children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")]
                        )

                    else:  # Default marker for other PileCodes
                        marker = dl.Marker(
                            position=(row["latitude"], row["longitude"]),
                            color=use_color, fill=True,fillOpacity=1.0,
                            children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")]
                        )
                    center = [row["latitude"], row["longitude"]]
                    markers.append(marker)

                    if not selected_pileid is None:  # Recenter on selected PileID
                        center = [row["latitude"], row["longitude"]]

        return markers, center,zoom_level, f"map-{center_lat}-{center_lon}-{zoom_level}"


    @app.callback(
        Output("time_graph", "figure"),
        Output("depth_graph", "figure"),
        Output('download-pdf-btn', 'disabled'),
        Input('pilelist-table', 'selectedRows'),
        Input('window-size', 'data'),
        # State("jobid-filter","value"),

    )
    def update_combined_graph(selected_row, window_size):
        if not selected_row:
            # No row selected - you might want to show all data or a default view
            return go.Figure(
                layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"}),go.Figure(
                layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"}) ,True # Dark background even if empty
        selected_row = selected_row[0]  # Get first selected row (since we're using single selection)
        selected_pileid = selected_row['PileID']
        selected_date = pd.to_datetime(selected_row['Time']).date().strftime(format='%Y-%m-%d')
        pile_info = pile_data[selected_pileid][selected_date]
        try:
            diameter = float(selected_row['PileDiameter'])
        except:
            diameter = None
        fig = ts.create_time_chart(pile_info)
        fig1 = ts.create_depth_chart(pile_info,diameter)

        # if not window_size is None:
        #     width = window_size['width']
        #     if width < 768:  # Mobile breakpoint
        #         fig1 = create_depth_chart_small_screen(pile_info,diameter)
        #     else:
        #         fig1 = create_depth_chart(pile_info, diameter)
        # else:
        #     fig1 = create_depth_chart(pile_info, diameter)

        return fig,fig1,False

    @app.callback(
        Output("pile-summary-cards", "children"),
        [Input('pilelist-table', 'selectedRows'), Input("jobid-filter", "value")]
        # [Input("pileid-filter", "value"), Input("jobid-filter", "value")],
        # State('date-filter','value')
    )
    # def update_summary_cards(selected_pileid, selected_jobid,selected_date):
    #     if not selected_pileid or not selected_jobid:
    #         return html.Div("Select a PileID to view statistics.", style={'color': 'white', 'textAlign': 'center'})
    def update_summary_cards(selected_row,selected_jobid):
        if not selected_row:
            return html.Div("Select a PileID to view statistics.", style={'color': 'white', 'textAlign': 'center'})

        selected_row = selected_row[0]  # Get first selected row (since we're using single selection)
        selected_pileid = selected_row['PileID']
        selected_date = pd.to_datetime(selected_row['Time']).date().strftime(format='%Y-%m-%d')
        # Filter data for the selected PileID
        filtered_df = properties_df[properties_df["PileID"] == selected_pileid]

        # Extract statistics
        move_time = filtered_df["MoveTime"].iloc[0] if "MoveTime" in filtered_df.columns else "N/A"
        move_distance = filtered_df["MoveDistance"].iloc[0] if "MoveDistance" in filtered_df.columns else "N/A"
        move_distance =round(move_distance,2)
        delay_time = filtered_df["DelayTime"].iloc[0] if "DelayTime" in filtered_df.columns else "N/A"
        if "OverBreak" in filtered_df.columns:
            overbreak = float(filtered_df['OverBreak'].iloc[0])
            overbreak = overbreak* 100 - 100.0
            overbreak = f"{overbreak :.0f}%"
        else:
            "N/A"

        title = f"JobID {selected_jobid} - PileID {selected_pileid} on {selected_date}"
        details = get_pile_details_cards(title, move_time, move_distance, delay_time, overbreak)
        return details

    @app.callback(
        Output("pile-summary-cards-jobid", "children"),
        [Input("jobid-filter", "value"),
         Input("date-filter", "value"),
         Input("rigid-filter", "value"),
         # Input("pileid-filter", "value"),
         Input('pilecode-filter', "value"),
         Input('pilestatus-filter', "value"),
         Input('piletype-filter', "value"),
         Input('productcode-filter', "value")
         ]
    )
    def update_summary_cards_jobid(selected_jobid,selected_date,selected_rigid,selected_pilecode, selected_pilestatus,selected_piletype,selected_productcode):
        if not selected_jobid:
            return html.Div("Select a JobID to view statistics.", style={'color': 'white', 'textAlign': 'center'})

        # Filter data for the selected PileID
        filtered_df = properties_df[properties_df["JobID"] == selected_jobid]

        if not selected_date is None:
            filtered_df=filtered_df[filtered_df['date']==selected_date]
        if not selected_rigid is None:
            filtered_df = filtered_df[filtered_df['RigID'] == selected_rigid]
        if not selected_pilecode is None:
            filtered_df = filtered_df[filtered_df['PileCode'] == selected_pilecode]
        if not selected_pilestatus is None:
            filtered_df = filtered_df[filtered_df['PileStatus'] == selected_pilestatus]
        if not selected_pilestatus is None:
            filtered_df = filtered_df[filtered_df['PileStatus'] == selected_pilestatus]
        if not selected_piletype is None:
            filtered_df = filtered_df[filtered_df['PileType'] == selected_piletype]
        if not selected_productcode is None:
            filtered_df = filtered_df[filtered_df['ProductCode'] == selected_productcode]

        # Extract statistics
        unique_pile_count = properties_df[properties_df["JobID"] == selected_jobid]["PileID"].nunique()
        unique_pile_count_filters = filtered_df['PileID'].nunique()

        # Create info cards
        return [
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.P("🔢 # Piles: " + str(unique_pile_count),
                                   className="card-title",
                                   style={"display": "flex", "alignItems": "center",
                                          "marginBottom": "0", "whiteSpace": "nowrap"}),  # Remove default margin
                        ]),
                        className="mb-3" # Reduced bottom margin
                    ),
                    xs=12, sm=6, md=6, lg=6, xl=6
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.P("🔢 # Piles filtered: " + str(unique_pile_count_filters),
                                   className="card-title",
                                   style={"display": "flex", "alignItems": "center",
                                          "marginBottom": "0", "whiteSpace": "nowrap"}),  # Remove default margin
                        ]),
                        className="mb-3"  # Reduced bottom margin
                    ),
                    xs=12, sm=6, md=6, lg=6, xl=6,
                    className="mt-2 mt-sm-0"  # Add top margin only on xs, remove on sm+
                )
            ])  # , className="g-2" Small gutter between columns when side-by-side
            ]


    # @app.callback(
    #     Output("save-message", "children"),
    #     Input("save-button", "n_clicks"),
    #     Input("pileid-filter", "value"),
    #     State("filtered-table", "data"),
    #     State("group-filter", "value"),
    #     prevent_initial_call=True
    # )
    # def save_changes(n_clicks, selected_pileid,table_data, selected_group):
    #     ctx = dash.callback_context  # Get the trigger
    #     triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
    #     if triggered_id=="pileid-filter":
    #         return ""
    #     if n_clicks > 0 and selected_group == "Edit":
    #         # Convert table data to a DataFrame
    #         df_edited = pd.DataFrame(table_data)
    #
    #         # Save only if there is data
    #         if not df_edited.empty:
    #             # df_edited.to_csv(os.path.join(file_path,"edited_data.csv"), index=False)  # Save to CSV file
    #             return "Changes saved successfully!"
    #
    #     return ""

    @app.callback(
        [Output("save-button", "style"),  # Show/Hide Save button
         Output("save-button", "disabled")],  # Disable after clicking
        [Input("group-filter", "value"),  # Trigger when Group changes
         Input("save-button", "n_clicks"),  # Track Save button clicks
         Input("pileid-filter", "value")],  # Reset on PileID change
        [State("save-button", "disabled")],  # Keep track of the disabled state
        prevent_initial_call=True
    )
    def toggle_save_button(selected_group, save_clicks, selected_pileid, is_disabled):
        # Show button only if "Edit" is selected
        button_style = {"display": "block"} if selected_group == "Edit" else {"display": "none"}

        # If PileID changes, re-enable the button
        if selected_pileid:
            return button_style, False

        # Disable only after clicking the button
        if save_clicks:
            return button_style, True

        raise PreventUpdate  # Prevent unnecessary updates


    # Callbacks to toggle each collapsible section
    @app.callback(
        Output("collapse-map", "is_open"),
        [Input("toggle-map", "n_clicks")],
        [State("collapse-map", "is_open")]
    )
    def toggle_map(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open

    @app.callback(
        Output("collapse-plots", "is_open"),
        [Input("toggle-plots", "n_clicks")],
        [State("collapse-plots", "is_open")]
    )
    def toggle_plots(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open

    @app.callback(
        Output("collapse_depth_plots", "is_open"),
        [Input("toggle_depth_plots", "n_clicks")],
        [State("collapse_depth_plots", "is_open")]
    )
    def toggle_plots(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open

    @app.callback(
        Output("collapse-views", "is_open"),
        [Input("toggle-views", "n_clicks")],
        [State("collapse-views", "is_open")]
    )
    def toggle_views(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open

    #
    @app.callback(
        Output("collapse-pilelist", "is_open"),
        [Input("toggle-pilelist", "n_clicks")],
        [State("collapse-pilelist", "is_open")]
    )
    def toggle_views(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open


    @app.callback(
        Output("download-csv", "data"),
        Input("btn_download", "n_clicks"),
        State("pilelist-table","rowData"),
        prevent_initial_call=True
    )
    def download_csv(n_clicks,data):
        if n_clicks:
            # Convert DataFrame to CSV in memory
            df = pd.DataFrame(data)
            csv_string = df.to_csv(index=False, encoding='utf-8')
            return dict(content=csv_string, filename=f"PileList_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv")


    @app.callback(
        Output("download-pdf", "data"),
        Input("download-pdf-btn", "n_clicks"),
        [State('pilelist-table', 'selectedRows'),
         State('time_graph', 'figure'),
         State('depth_graph', 'figure')],
        prevent_initial_call=True
    )
    def generate_pdf_callback(n_clicks, selected_rows, time_fig, depth_fig):
        if not n_clicks or not selected_rows:
            return no_update

        selected_row = selected_rows[0]
        try:
            return ts.generate_mwd_pdf(selected_row, time_fig, depth_fig)
        except Exception as e:
            print(f"PDF generation failed: {str(e)}")
            return no_update



    # @app.callback(
    #     Output("task-id", "data"),
    #     Output("check-task-interval", "disabled"),
    #     Input("download-ALL-pdf-btn", "n_clicks"),
    #     State('pilelist-table', 'rowData'),
    #     prevent_initial_call=True
    # )
    # def start_background_pdf_task(n_clicks, all_rows):
    #     if not n_clicks or not all_rows:
    #         return no_update, True
    #
    #     task = generate_all_pdfs_task.apply_async(args=[all_rows, pile_data])
    #     return task.id, False  # Enable interval to start polling
    #
    # @app.callback(
    #     Output("download-ALL-pdf", "data"),
    #     Output("check-task-interval", "disabled"),
    #     Output("task-status", "children"),
    #     Input("check-task-interval", "n_intervals"),
    #     State("task-id", "data"),
    #     prevent_initial_call=True
    # )
    # def check_task_status(n, task_id):
    #     if not task_id:
    #         return no_update, True, ""
    #
    #     from tasks import celery_app
    #     task_result = celery_app.AsyncResult(task_id)
    #
    #     if task_result.state == 'PENDING':
    #         return no_update, False, "Generating PDFs..."
    #     elif task_result.state == 'SUCCESS':
    #         result = task_result.result
    #         return result, True, "✅ Download ready!"
    #     elif task_result.state == 'FAILURE':
    #         return no_update, True, "❌ Task failed!"
    #     else:
    #         return no_update, False, f"⏳ Status: {task_result.state}"

    # @app.callback(
    #     output=[
    #         Output("download-ALL-pdf", "data"),
    #         Output("task-status", "children")
    #     ],
    #     inputs=Input("download-ALL-pdf-btn", "n_clicks"),
    #     state=[State('pilelist-table', 'rowData')],
    #     background=True,  # Run in background via Celery
    #     manager=background_callback_manager,
    #     prevent_initial_call=True,
    # )
    # def generate_pdfs_in_background(n_clicks, all_rows):
    #     if not n_clicks or not all_rows:
    #         return None, "⚠️ No rows selected."
    #     result = generate_all_pdfs_task(all_rows,pile_data)
    #     # task = generate_all_pdfs_task.apply_async(args=[all_rows,pile_data])
    #     # result = task.get(timeout=600)  # Wait for the Celery task to complete
    #
    #     if not result:
    #         return None, "❌ PDF generation failed."
    #
    #     return result, "✅ Download ready!"


    # @app.callback(
    #     output=[
    #         Output("download-ALL-pdf", "data"),
    #         Output("task-status", "children"),
    #     ],
    #     inputs=Input("download-ALL-pdf-btn", "n_clicks"),
    #     state=[State('pilelist-table', 'rowData')],
    #     background=True,
    #     manager=background_callback_manager,
    #     prevent_initial_call=True,
    # )
    # def generate_pdfs_in_background(n_clicks, all_rows):
    #     if not n_clicks or not all_rows:
    #         raise PreventUpdate
    #
    #     try:
    #         # Your existing function
    #         result = ts.generate_all_pdfs_task(all_rows, pile_data)
    #         return result, "✅ PDF generation complete!"
    #     except Exception as e:
    #         return None, f"❌ Error: {str(e)}"

    @app.callback(
        Output("task-id", "data"),
        inputs=Input("download-ALL-pdf-btn", "n_clicks"),
        state = [State('pilelist-table', 'rowData')],
        background=True,
        manager=background_callback_manager,
        prevent_initial_call=True,

    )
    def start_task(n_clicks, all_rows):
        if not n_clicks or not all_rows:
            raise PreventUpdate
        try:
            task = ts.generate_all_pdfs_task.delay(args=[all_rows, pile_data])
            return task.id
                    # , "✅ PDF generation complete!")
        except Exception as e:
            return None
                    # , f"❌ Error: {str(e)}")


    # @app.callback(
    #     Output("task-status", "children"),
    #     Output("poll-interval", "disabled"),
    #     Input("poll-interval", "n_intervals"),
    #     Input("task-id", "data"),
    #     prevent_initial_call=True
    # )
    # def poll_status(n, task_id):
    #     from celery.result import AsyncResult
    #     task = AsyncResult(task_id)
    #     if task.ready():
    #         return f"Done: {task.result}", True
    #     return "Processing...", False

    @app.callback(
        Output("task-status", "children"),
        Input("poll-interval", "n_intervals"),
        State("task-id-store", "data")
    )
    def poll_status(n, task_id):
        if not task_id:
            raise dash.exceptions.PreventUpdate

        task = AsyncResult(task_id)
        if task.ready():
            if task.successful():
                return "✅ Task complete!"
            else:
                return "❌ Task failed."
        return "⏳ Processing..."

    # Run the app
    return app