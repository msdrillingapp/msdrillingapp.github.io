import dash
import pandas as pd
from dash.exceptions import PreventUpdate
from dash import no_update

from dash import dcc, html, Output, Input, ctx, dash_table,callback_context,MATCH, State,ClientsideFunction

import plotly.express as px
import plotly.graph_objects as go
import os
from utility_funtions import *
import dash_auth
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from datetime import timedelta, datetime
from plotly.subplots import make_subplots
from layouts import get_filters,get_pilelist,get_pile_details_cards,get_header,get_filtered_table
# Keep this out of source code repository - save in a file or a database
VALID_USERNAME_PASSWORD_PAIRS = {
    'Dennis': 'Meara'
}

#####################
# Folder containing GeoJSON files
file_path = os.path.join(os.getcwd(), "assets",)
geojson_folder = os.path.join(file_path,'data')
# # Create a dictionary to map Field to Group
groups_df = pd.read_csv(os.path.join(file_path,'Groups.csv'))
groups_df = groups_df.explode("Group").reset_index(drop=True)
title_text = "Morris-Shea Drilling App"

# Load all datasets
properties_df, pile_data,latitudes,longitudes,markers = load_geojson_data()

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

# Create Dash app
app = dash.Dash(__name__, external_stylesheets=["/assets/style.css",dbc.themes.BOOTSTRAP],suppress_callback_exceptions=True,
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.2, minimum-scale=0.5,'}])
app.title = 'MS Drill Tracker'
server = app.server
# auth = dash_auth.BasicAuth(
#     app,
#     VALID_USERNAME_PASSWORD_PAIRS
# )
flts = get_filters(properties_df)
pilelist =get_pilelist()
header = get_header()
filtered_table = get_filtered_table()
app.layout = html.Div([
    # ============================================================
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
                   # style={'width': '100%', 'height': '400px', 'align': 'center', 'marginleft': '10px', 'display': 'flex',
                   #    'justifyContent': 'center'}),
            id="collapse-map",
            is_open=True
        ),
    ]),
    # ======================================================
    html.Br(),
# =====================================================================================
    pilelist,

    # ======================================================
    # html.Br(),

    # ===============================================
    html.Div([
        # Statistics Info Cards
        html.Div(id="pile-summary-cards", style={
            'display': 'flex', 'justifyContent': 'space-around', 'alignItems': 'center',
            'backgroundColor': '#193153', 'color': 'white', 'padding': '10px',
            'borderRadius': '5px', 'marginTop': '10px'
        }),
    ]),
    # ===============================================
    # Table & Chart Side by Side
    html.Div([
        # Plots Section
        dbc.Button("Show Time Plot", id="toggle-plots", color="primary", className="mb-2", style={"marginTop": "20px"}),
        dbc.Collapse(
            dcc.Graph(id="time_graph", style={"height": "500px", "backgroundColor": "#193153"}),
            id="collapse-plots",
            is_open=False
        ),
        dbc.Button("Show Depth Plots", id="toggle_depth_plots", color="primary", className="mb-2", style={"marginTop": "20px"}),
        dbc.Collapse(
            dcc.Graph(id="depth_graph", style={"height": "500px", "backgroundColor": "#193153"}),
            # dcc.Store(id='stored-figure_depth'),
            # dcc.Download(id="download-pdf"),
            # html.Button("Export to PDF", id="btn-pdf"),
            id="collapse_depth_plots",
            is_open=False
        ),

    # ]),
    # =======================================================================
    # html.Div([
        # Views Section (Main Table)
        dbc.Button("Show Table", id="toggle-views", color="primary", className="mb-2", style={"marginTop": "20px"}),

        dbc.Collapse(
            html.Div([
                dbc.Row([
                    # dbc.Col(
                    #         html.Div([
                    #         html.Label("Select PileID:", style={'color': 'white'}),
                    #         dcc.Dropdown(
                    #             id="pileid-filter-top",
                    #             placeholder="Filter by PileID",
                    #             style={'marginBottom': '5px', 'marginRight': '5px', 'marginLeft': '5px'},
                    #             className="dark-dropdown"
                    #         ),]),
                    #     xs=10, sm=5, md=8, lg=3, xl=3  # Move these properties outside as well
                    # ),
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
                # dash_table.DataTable(
                #     id="filtered-table",
                #     columns=[
                #         {"name": "Field", "id": "Field", "editable": False},
                #         {"name": "Value", "id": "Value", "editable": True, "presentation": "input"}
                #     ],
                #     data=[],
                #     filter_action="none",
                #     sort_action=None,
                #     page_size=10,
                #     style_table={'overflowX': 'auto', 'width': '75%', 'margin': 'auto', 'border': '1px grey'},
                #     style_cell={'textAlign': 'left', 'color': 'white', 'backgroundColor': '#193153'},
                #     style_header={'fontWeight': 'bold', 'backgroundColor': '#1f4068', 'color': 'white'}
                # ),
                html.Br(),
        #         html.Div(
        #             id="edit-options-container",
        #             children=[
        #                 html.Label("Delay", id='delay-label', style={"color": "white", "fontWeight": "bold"}),
        #                 dcc.Dropdown(
        #                     id="edit-options",
        #                     options=[
        #                         {"label": "Waiting on Concrete", "value": "Waiting on Concrete"},
        #                         {"label": "Site access", "value": "Site access"},
        #                         {"label": "Layout", "value": "Layout"},
        #                         {"label": "Enter free text", "value": "free_text"}],
        #                     placeholder="Select an option",
        #                     style={"display": "none", "width": "300px"},
        #                     className="dark-dropdown"
        #                 ),
        #                 dcc.Input(
        #                     id="free-text-input",
        #                     type="text",
        #                     placeholder="Enter text",
        #                     style={"display": "none", "width": "300px"}
        #                 )
        #             ]
        # ),
        # html.Button("Approve Status", id="save-button", n_clicks=0, style={
        #     'marginTop': '10px', 'padding': '10px 15px', 'fontSize': '16px',
        #     'cursor': 'pointer', 'backgroundColor': '#28a745', 'color': 'white',
        #     'border': 'none', 'borderRadius': '5px'
        # }),
        # html.Div(id="save-message", style={'marginTop': '10px', 'color': 'white'}),
                ]),
                id="collapse-views",
                is_open=False
            )


        ]),
    # ,style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'}
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
# def update_table(selected_pileid, selected_date, selected_group):
#     if not selected_pileid or not selected_date:
def update_table(selected_row, selected_group):
    if not selected_row:
        return []  # Return an empty table before selection
    filtered_df = merged_df.copy()

    selected_row = selected_row[0]  # Get first selected row (since we're using single selection)
    selected_pileid = selected_row['PileID']
    selected_date = pd.to_datetime(selected_row['Time']).date().strftime(format='%Y-%m-%d')
    # Filter DataFrame based on selected PileID and Date
    filtered_df = filtered_df[(filtered_df["PileID"] == selected_pileid) & (filtered_df["date"] == selected_date)]

    # # Custom Order for "Edit" Group
    # custom_order = [
    #     "PileID", "LocationID", "PileLength", "MaxStroke",
    #     "PumpID", "PumpCalibration", "PileStatus","PileCode","WorkingGrade", "Comments", "Delay"
    # ]
    # "ProductCode""OverBreak",
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
        out_dict['OverBreak'] = f"{overbreak :.2f}%"
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

        # Custom Order for "Edit" Group
    # columns = [
    #     "PileID","Depth", "MaxStroke", "PileStatus","PileCode", "Comments"
    # ]
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
            "OverBreak": f"{(row['OverBreak'] - 1) * 100:.2f}%",
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


        }
        summary_data.append(dict_data)
    # out = filtered_df[columns].to_dict("records")
    # out_dict = {item['Field']: item['Value'] for item in out}

    # Modify OverBreak if it exists
    # if 'OverBreak' in out_dict:
    #     overbreak = float(out_dict['OverBreak'])
    #     overbreak = overbreak* 100-100.0
    #     out_dict['OverBreak'] = f"{overbreak :.2f}%"
    #
    # # Convert back to list of dictionaries
    # out = [{'Field': k, 'Value': v} for k, v in out_dict.items()]

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

    center = [np.nanmean(list(filter_none(properties_df["latitude"]))), np.nanmean(list(filter_none(properties_df["longitude"])))]
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

        center = [np.nanmean(list(filter_none(filtered_df["latitude"]))), np.nanmean(list(filter_none(filtered_df["longitude"])))]  # Default center

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

# Callback to track edited values and highlight changes
# @app.callback(
#     Output("filtered-table", "style_data_conditional"),
#     [Input("filtered-table", "data_previous"), Input("group-filter", "value")],
#     State("filtered-table", "data"),prevent_initial_call=True
# )
# def highlight_changes(prev_data, selected_group, current_data):
#     if not prev_data or not selected_group:
#         return []
#
#     styles = []
#     changed_values[selected_group] = set()
#     for i, (prev_row, curr_row) in enumerate(zip(prev_data, current_data)):
#         if prev_row["Value"] != curr_row["Value"] and selected_group=='Edit':
#             changed_values[selected_group].add(i)
#
#     styles.extend([
#         {"if": {"row_index": i, "column_id": "Value"}, "color": "#ffcc00", "fontWeight": "bold"}
#         for i in changed_values.get(selected_group, [])
#     ])
#
#     return styles



# Callback to update the combined graph
# @app.callback(
#     Output("time_graph", "figure"),
#     [Input("pileid-filter", "value"), Input("date-filter", "value")],
#     State("jobid-filter","value")
# )
# def update_combined_graph(selected_pileid, selected_date,selected_jobid):
#     if not selected_pileid or selected_pileid not in pile_data or selected_date not in pile_data[selected_pileid]:
#         return go.Figure(
#             layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"}) # Dark background even if empty
#
#     pile_info = pile_data[selected_pileid][selected_date]
#
#     # Create figure with two y-axes
#     fig = px.line(title=f"JobID {selected_jobid} - PileID {selected_pileid} on {selected_date}")
#     time_interval = pd.to_datetime(pile_info["Time"]).to_pydatetime()
#     minT = min(time_interval)-timedelta(minutes=2)
#     maxT = max(time_interval)+timedelta(minutes=2)
#     minT=minT.strftime(format='%Y-%m-%d %H:%M:%S')
#     maxT = maxT.strftime(format='%Y-%m-%d %H:%M:%S')
#     # Add Depth vs Time (Secondary Y-Axis)
#     fig.add_scatter(
#         x=pile_info["Time"],
#         y=pile_info["Depth"],
#         mode="lines",
#         name="Depth",
#         yaxis="y1",
#         line_color="#f7b500"
#     )
#
#     # Add Strokes vs Time (Primary Y-Axis)
#     fig.add_scatter(
#         x=pile_info["Time"],
#         y=pile_info["Strokes"],
#         mode="lines",
#         name="Strokes",
#         yaxis="y2",
#         line_color="green"
#
#     )
#
#     # Update layout for dual y-axes and dark background
#     fig.update_layout(
#         xaxis_title="Time",
#         yaxis=dict(title="Depth", side="left", showgrid=True),
#         yaxis2=dict(title="Strokes", overlaying="y", side="right", showgrid=False),
#         plot_bgcolor="#193153",
#         paper_bgcolor="#193153",
#         font=dict(color="white"),
#         xaxis_range=[minT, maxT],
#         # yaxis_range = [min(pile_info['Depth'])-5,max(pile_info['Depth'])+5],
#         # yaxis2_range=[min(pile_info['Strokes']) - 5, max(pile_info['Strokes']) + 5],
#
#     )
#
#
#     return fig

# @app.callback(
#     Output("depth_graph", "figure"),
#     [Input("pileid-filter", "value"), Input("date-filter", "value")],
#     State("jobid-filter","value")
# )
# def update_depth_graph(selected_pileid, selected_date,selected_jobid):
#     if not selected_pileid or selected_pileid not in pile_data or selected_date not in pile_data[selected_pileid]:
#         return go.Figure(
#             layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"}) # Dark background even if empty
#
#     pile_info = pile_data[selected_pileid][selected_date]
#
#     # Create figure with two y-axes
#     # fig1 = px.line(title=f"JobID {selected_jobid} - PileID {selected_pileid} on {selected_date}")
#     minD = min(pile_info['Depth'])-5
#     maxD = max(pile_info['Depth'])+5
#     # ================================================================================
#     # Create subplots with shared y-axis
#     fig1 = make_subplots(rows=1, cols=5, shared_yaxes=True,
#                         subplot_titles=("Penetration Rate", "Rotary Head Pressure", "Pulldown", "Rotation"))
#
#     # Add traces
#     increasing_PR,increasing_D,decreasing_PR,decreasing_D = indrease_decrease_split(pile_info["PenetrationRate"],pile_info["Depth"])
#     fig1.add_trace(go.Scatter(x=increasing_PR, y=increasing_D, mode='lines',line=dict(color='red', width=2), name='UP'), row=1,col=1)
#     fig1.add_trace(go.Scatter(x=decreasing_PR, y=decreasing_D, mode='lines', line=dict(color='blue', width=2),name='DOWN'), row=1, col=1)
#     # fig1.add_trace(go.Scatter(x=pile_info["PenetrationRate"], y=pile_info["Depth"], mode='lines', name='PenetrationRate'), row=1, col=1)
#     increasing_RP, increasing_D, decreasing_RP, decreasing_D = indrease_decrease_split(pile_info["RotaryHeadPressure"],pile_info["Depth"])
#     fig1.add_trace(go.Scatter(x=increasing_RP, y=increasing_D, mode='lines', line=dict(color='red', width=2),showlegend=False),row=1, col=2)
#     fig1.add_trace(go.Scatter(x=decreasing_RP, y=decreasing_D, mode='lines', line=dict(color='blue', width=2),showlegend=False),row=1, col=2)
#     # fig1.add_trace(go.Scatter(x=pile_info['RotaryHeadPressure'], y=pile_info["Depth"], mode='lines', name='RotaryHeadPressure'), row=1, col=2)
#     increasing_Pull, increasing_D, decreasing_Pull, decreasing_D = indrease_decrease_split(pile_info["Pulldown"],pile_info["Depth"])
#     fig1.add_trace(go.Scatter(x=increasing_Pull, y=increasing_D, mode='lines', line=dict(color='red', width=2),showlegend=False), row=1,col=3)
#     fig1.add_trace(go.Scatter(x=decreasing_Pull, y=decreasing_D, mode='lines', line=dict(color='blue', width=2),showlegend=False), row=1,col=3)
#     # fig1.add_trace(go.Scatter(x=pile_info['Pulldown'], y=pile_info["Depth"], mode='lines', name='Pulldown'), row=1, col=3)
#     increasing_Rot, increasing_D, decreasing_Rot, decreasing_D = indrease_decrease_split(pile_info["Rotation"],pile_info["Depth"])
#     fig1.add_trace(go.Scatter(x=increasing_Rot, y=increasing_D, mode='lines', line=dict(color='red', width=2),showlegend=False), row=1, col=4)
#     fig1.add_trace(go.Scatter(x=decreasing_Rot, y=decreasing_D, mode='lines', line=dict(color='blue', width=2),showlegend=False), row=1, col=4)
#     # fig1.add_trace(go.Scatter(x=pile_info['Rotation'], y=pile_info["Depth"], mode='lines', name='Rotation'), row=1, col=4)
#
#     # Update layout for dual y-axes and dark background
#     fig1.update_layout(
#         yaxis_title="Depth (ft)",
#         # yaxis=dict(title="Depth", side="left", showgrid=False),
#         # yaxis2=dict(title="Strokes", overlaying="y", side="right", showgrid=False),
#         plot_bgcolor="#193153",
#         paper_bgcolor="#193153",
#         font=dict(color="white"),
#         # yaxis_range=[minD, maxD]
#     )
#
#     fig1.update_yaxes(range=[minD, maxD])
#     tils = ['(ft/min)','(bar)','(tons)','(rpm)']
#     for i in range(0, 4):
#         fig1.update_xaxes(title_text=tils[i] , row=1, col=i+1)
#
#     return fig1

@app.callback(
    Output("time_graph", "figure"),
    Input('pilelist-table', 'selectedRows'),
    State("jobid-filter","value")
)
def update_combined_graph(selected_row, selected_jobid):
    if not selected_row:
        # No row selected - you might want to show all data or a default view
        return go.Figure(
            layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"})  # Dark background even if empty
    selected_row = selected_row[0]  # Get first selected row (since we're using single selection)
    selected_pileid = selected_row['PileID']
    selected_date = pd.to_datetime(selected_row['Time']).date().strftime(format='%Y-%m-%d')
    pile_info = pile_data[selected_pileid][selected_date]

    # Create figure with two y-axes
    # fig = px.line(title=f"JobID {selected_jobid} - PileID {selected_pileid} on {selected_date}")
    fig = px.line(title='')
    time_interval = pd.to_datetime(pile_info["Time"]).to_pydatetime()
    minT = min(time_interval)-timedelta(minutes=2)
    maxT = max(time_interval)+timedelta(minutes=2)
    minT=minT.strftime(format='%Y-%m-%d %H:%M:%S')
    maxT = maxT.strftime(format='%Y-%m-%d %H:%M:%S')
    # Add Depth vs Time (Secondary Y-Axis)
    fig.add_scatter(
        x=pile_info["Time"],
        y=pile_info["Depth"],
        mode="lines",
        name="Depth",
        yaxis="y1",
        line_color="#f7b500"
    )

    # Add Strokes vs Time (Primary Y-Axis)
    fig.add_scatter(
        x=pile_info["Time"],
        y=pile_info["Strokes"],
        mode="lines",
        name="Strokes",
        yaxis="y2",
        line_color="green"

    )

    # Update layout for dual y-axes and dark background
    fig.update_layout(
        xaxis_title="Time",
        yaxis=dict(title="Depth", side="left", showgrid=True),
        yaxis2=dict(title="Strokes", overlaying="y", side="right", showgrid=False),
        plot_bgcolor="#193153",
        paper_bgcolor="#193153",
        font=dict(color="white"),
        xaxis_range=[minT, maxT],
        # yaxis_range = [min(pile_info['Depth'])-5,max(pile_info['Depth'])+5],
        # yaxis2_range=[min(pile_info['Strokes']) - 5, max(pile_info['Strokes']) + 5],

    )


    return fig
@app.callback(
    Output("depth_graph", "figure"),
    Input('pilelist-table', 'selectedRows')
)
def update_depth_graph(selected_row):
    if not selected_row:
        # No row selected - you might want to show all data or a default view
        return go.Figure(
            layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"}) # Dark background even if empty
    selected_row = selected_row[0]  # Get first selected row (since we're using single selection)
    selected_pileid = selected_row['PileID']
    selected_date = pd.to_datetime(selected_row['Time']).date().strftime(format='%Y-%m-%d')

    pile_info = pile_data[selected_pileid][selected_date]

    # Create figure with two y-axes
    # fig1 = px.line(title=f"JobID {selected_jobid} - PileID {selected_pileid} on {selected_date}")
    minD = min(pile_info['Depth'])-5
    maxD = max(pile_info['Depth'])+5
    # ================================================================================
    # Create subplots with shared y-axis
    fig1 = make_subplots(rows=1, cols=5, shared_yaxes=True,
                        subplot_titles=("Penetration Rate", "Rotary Head Pressure", "Pulldown", "Rotation"))

    # Add traces
    increasing_PR,increasing_D,decreasing_PR,decreasing_D = indrease_decrease_split(pile_info["PenetrationRate"],pile_info["Depth"])
    fig1.add_trace(go.Scatter(x=increasing_PR, y=increasing_D, mode='lines',line=dict(color='red', width=2), name='UP'), row=1,col=1)
    fig1.add_trace(go.Scatter(x=decreasing_PR, y=decreasing_D, mode='lines', line=dict(color='blue', width=2),name='DOWN'), row=1, col=1)
    # fig1.add_trace(go.Scatter(x=pile_info["PenetrationRate"], y=pile_info["Depth"], mode='lines', name='PenetrationRate'), row=1, col=1)
    increasing_RP, increasing_D, decreasing_RP, decreasing_D = indrease_decrease_split(pile_info["RotaryHeadPressure"],pile_info["Depth"])
    fig1.add_trace(go.Scatter(x=increasing_RP, y=increasing_D, mode='lines', line=dict(color='red', width=2),showlegend=False),row=1, col=2)
    fig1.add_trace(go.Scatter(x=decreasing_RP, y=decreasing_D, mode='lines', line=dict(color='blue', width=2),showlegend=False),row=1, col=2)
    # fig1.add_trace(go.Scatter(x=pile_info['RotaryHeadPressure'], y=pile_info["Depth"], mode='lines', name='RotaryHeadPressure'), row=1, col=2)
    increasing_Pull, increasing_D, decreasing_Pull, decreasing_D = indrease_decrease_split(pile_info["Pulldown"],pile_info["Depth"])
    fig1.add_trace(go.Scatter(x=increasing_Pull, y=increasing_D, mode='lines', line=dict(color='red', width=2),showlegend=False), row=1,col=3)
    fig1.add_trace(go.Scatter(x=decreasing_Pull, y=decreasing_D, mode='lines', line=dict(color='blue', width=2),showlegend=False), row=1,col=3)
    # fig1.add_trace(go.Scatter(x=pile_info['Pulldown'], y=pile_info["Depth"], mode='lines', name='Pulldown'), row=1, col=3)
    increasing_Rot, increasing_D, decreasing_Rot, decreasing_D = indrease_decrease_split(pile_info["Rotation"],pile_info["Depth"])
    fig1.add_trace(go.Scatter(x=increasing_Rot, y=increasing_D, mode='lines', line=dict(color='red', width=2),showlegend=False), row=1, col=4)
    fig1.add_trace(go.Scatter(x=decreasing_Rot, y=decreasing_D, mode='lines', line=dict(color='blue', width=2),showlegend=False), row=1, col=4)
    # fig1.add_trace(go.Scatter(x=pile_info['Rotation'], y=pile_info["Depth"], mode='lines', name='Rotation'), row=1, col=4)

    # Update layout for dual y-axes and dark background
    fig1.update_layout(
        yaxis_title="Depth (ft)",
        # yaxis=dict(title="Depth", side="left", showgrid=False),
        # yaxis2=dict(title="Strokes", overlaying="y", side="right", showgrid=False),
        plot_bgcolor="#193153",
        paper_bgcolor="#193153",
        font=dict(color="white"),
        # yaxis_range=[minD, maxD]
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,  # position below the plot
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0.5)",  # semi-transparent background
            font=dict(size=12),  # adjust font size
            itemwidth=30,  # control item width
        )
    )

    fig1.update_yaxes(range=[minD, maxD])
    tils = ['(ft/min)','(bar)','(tons)','(rpm)']
    for i in range(0, 4):
        fig1.update_xaxes(title_text=tils[i] , row=1, col=i+1)

    return fig1
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
        overbreak = f"{overbreak :.2f}%"
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
        # html.Div([html.P("🔢 Piles in JobID"), html.H4(unique_pile_count)], style={'textAlign': 'center', 'padding': '10px'}),
        # html.Div([html.P("🔢 Piles count with Filters"), html.H4(unique_pile_count_filters)],style={'textAlign': 'center', 'padding': '10px'})



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

# @app.callback(
#     Output("filtered-table", "columns"),
#     [Input("group-filter", "value")],
#     prevent_initial_call=True
# )
# # , Output("filtered-table", "dropdown_conditional")
# def update_columns(selected_group):
#     if selected_group == "Edit":
#         columns = [
#             {"name": "Field", "id": "Field", "editable": False},
#             {"name": "Value", "id": "Value", "editable": False},
#             {"name": "Edited Value", "id": "Edited Value", "editable": True, "presentation": "input"}
#         ]
#
#     else:
#         columns = [
#             {"name": "Field", "id": "Field", "editable": False},
#             {"name": "Value", "id": "Value", "editable": False}
#         ]
#
#
#     return columns#, dropdown_conditional
# =======================================================================================
# @app.callback(
#     [
#         Output("date-filter", "value"),
#         Output("rigid-filter", "value"),
#         Output("pilecode-filter", "value"),
#         Output("pilestatus-filter", "value"),
#         Output("piletype-filter", "value"),
#         Output("pileid-filter", "value"),
#         Output("pileid-filter-top", "value"),
#         Output("jobid-filter", "value"),
#
#         # Output("group-filter", "value")
#     ],
#     Input("reset-button", "n_clicks"),prevent_initial_call=True
# )
#
# def reset_filters(n_clicks):
#     if n_clicks > 0:
#         return None, None,None,None, None,None,None,None         # Reset all filters to default (empty)
#     return dash.no_update  # Don't change anything if the button hasn't been clicked
# ====================================================
# Callback to show/hide dropdown and input field
# @app.callback(
#     [Output("edit-options", "style"),
#      Output("free-text-input", "style")],
#     [Input("group-filter", "value"),
#      Input("edit-options", "value")]
# )
# def toggle_dropdown(selected_group, selected_option):
#     if selected_group == "Edit":
#         dropdown_style = {"display": "block", "width": "300px", "padding": "5px","backgroundColor": "#1f4068", "color": "white"}  # Show dropdown
#         input_style = {"display": "none", "width": "300px", "padding": "5px","backgroundColor": "#1f4068", "color": "white"}  # Hide input initially
#
#         if selected_option == "free_text":
#             input_style = {"display": "block", "width": "300px", "padding": "5px","backgroundColor": "#1f4068", "color": "white"}  # Show input field
#             dropdown_style = {"display": "none", "width": "300px", "padding": "5px","backgroundColor": "#1f4068", "color": "white"}  # Hide dropdown
#
#         return dropdown_style, input_style
#
#     return {"display": "none"}, {"display": "none"}  # Hide both if group isn't "Edit"

# @app.callback(
#     [Output("delay-label", "style"),
#      Output("edit-options", "style"),
#      Output("edit-options-container", "style"),Output("free-text-input", "style")],
#     [Input("group-filter", "value"), Input("edit-options", "value")]  # Assuming this is the dropdown that selects the group
# )
# def toggle_edit_dropdown(selected_group, selected_option):
#     if selected_group == "Edit":
#         visible_style = {"color": "white", "fontWeight": "bold", "marginBottom": "5px"}  # Show label
#         dropdown_style = {"display": "block", "width": "300px", "padding": "5px", "backgroundColor": "#1f4068","color": "white"}  # Show dropdown
#         input_style = {"display": "none", "width": "300px", "padding": "5px","backgroundColor": "#1f4068", "color": "white"}  # Hide input initially  # Show dropdown
#         container_style = {"display": "flex", "flexDirection": "column", "alignItems": "flex-start"}  # Show container
#         if selected_option == "free_text":
#                 input_style = {"display": "block", "width": "300px", "padding": "5px","backgroundColor": "#1f4068", "color": "white"}  # Show input field
#                 dropdown_style = {"display": "none", "width": "300px", "padding": "5px","backgroundColor": "#1f4068", "color": "white"}  # Hide dropdown
#         return visible_style, dropdown_style, container_style,input_style
#     else:
#         hidden_style = {"display": "none"}
#         return hidden_style, hidden_style, hidden_style ,hidden_style # Hide everything
#
#     return visible_style, dropdown_style, container_style,input_style


# @app.callback(
#     [Output("edit-options", "value"),  # Reset Delay dropdown
#      Output("group-filter", "value")],  # Reset Group filter
#     Input("pileid-filter", "value") ,
#     prevent_initial_call=True # Trigger when PileID changes
# )
# def reset_dropdowns(selected_pileid):
#     return None, None  # Reset values


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
    Input("btn-pdf", "n_clicks"),
    State('pilelist-table', 'selectedRows'),
    prevent_initial_call=True
)
def download_charts(click,selected_row):
    if not selected_row:
        return no_update
    return

# Run the app
if __name__ == "__main__":
    # app.run(debug=True)
    app.run(debug=False)

#
