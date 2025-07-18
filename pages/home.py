import dash
import os

from dash import dcc, html, Output, Input, State,no_update,callback,ClientsideFunction,DiskcacheManager, CeleryManager
# from dash import no_update,callback, register_page
from datetime import datetime
import numpy as np
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate
import pandas as pd
from functions import properties_df, latitudes,longitudes,markers,jobid_pile_data,merged_df,groups_list
from layouts import get_filters,get_pilelist,get_pile_details_cards,get_header,get_filtered_table,add_charts
from functions import generate_all_pdfs_task,generate_mwd_pdf, filter_none, create_time_chart,create_depth_chart
import dash_bootstrap_components as dbc
# import functions as ts
from celery.result import AsyncResult
import dash_leaflet as dl
from celery_config import celery_app

dash.register_page(__name__,'/')

if '__file__' in globals():
    root_path = os.path.dirname(os.path.abspath(__file__))
else:
    # Fallback for environments where __file__ isn't available
    root_path = os.getcwd()
# Track changed values
changed_values ={}

# Calculate map center and zoom
if latitudes and longitudes:
    center_lat = np.nanmean([float(item) for item in latitudes if item is not None])
    center_lon = np.nanmean([float(item) for item in longitudes if item is not None])
    map_center = [center_lat, center_lon]
    zoom_level = 8  # Adjust zoom for a closer view
else:
    map_center = [40, -100]
    zoom_level = 4

flts = get_filters(properties_df)
pilelist = get_pilelist()
# header = get_header()
charts = add_charts()
filtered_table = get_filtered_table()
layout = html.Div([
    # ============================================================
    dcc.Store(id='window-size', data={'width': 1200}),
    # header,
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

], style={'backgroundColor': '#193153', 'height': '650vh', 'padding': '20px', 'position': 'relative'})

# ================================================================================================
# ================================================================================================
# ================================================================================================
# @clientside_callback(
#     ClientsideFunction(namespace="clientside", function_name="scrollToTop"),
#     Output("scroll-top-button", "n_clicks"),
#     Input("scroll-top-button", "n_clicks")
# )
# # Callback to filter table
def check_is_none(mdict,name_var):
    if name_var in mdict:
        try:
            val = mdict[name_var]
            mdict[name_var] = round(float(val), 1) if val is not None and val == val else 0.0
        except (ValueError, TypeError):
            mdict[name_var] = 0.0  # or None
    return mdict


@callback(
    # Output("filtered-table", "data"),
    Output("filtered-table", "rowData"),
    # [Input("pileid-filter", "value"),
    #  Input("date-filter", "value"),
    [ Input('pilelist-table', 'selectedRows'),
     Input("group-filter", "value")],prevent_initial_call=True,
)
def update_table(selected_row, selected_group):
    if not selected_row:
        raise PreventUpdate
        # return []  # Return an empty table before selection
    filtered_df = merged_df.copy()

    selected_row = selected_row[0]  # Get first selected row (since we're using single selection)
    selected_pileid = selected_row['PileID']
    selected_date = pd.to_datetime(selected_row['Time']).date().strftime(format='%Y-%m-%d')
    # Filter DataFrame based on selected PileID and Date
    filtered_df = filtered_df[(filtered_df["PileID"] == selected_pileid) & (filtered_df["date"] == selected_date)]

    if not selected_group is None:
        filtered_df = filtered_df[filtered_df["Group"] == selected_group]

    out = filtered_df[["Field", "Value"]].to_dict("records")
    out_dict = {item['Field']: item['Value'] for item in out}

    # Modify OverBreak if it exists
    if 'OverBreak' in out_dict:
        overbreak = float(out_dict['OverBreak'])
        overbreak = overbreak* 100-100.0
        out_dict['OverBreak'] = f"{overbreak :.0f}%"

    out_dict = check_is_none(out_dict,'MoveDistance')

    if 'PileArea' in out_dict:
        value = round(float(out_dict['PileArea']),1)
        out_dict['PileArea'] = value
    if 'PileVolume' in out_dict:
        value = round(float(out_dict['PileVolume']),1)
        out_dict['PileVolume'] = value
    if 'GroutVolume' in out_dict:
        value = round(float(out_dict['GroutVolume']), 1)
        out_dict['GroutVolume'] = value

    # Convert back to list of dictionaries
    out = [{'Field': k, 'Value': v} for k, v in out_dict.items()]

    return out

@callback(
    Output("pilelist-table", "rowData"),
    [Input("jobid-filter", "value"),
     Input("date-filter", "value"),
     Input("rigid-filter", "value")],
    prevent_initial_call=True,
)
def update_table(selected_jobid, selected_date,selected_rigid):
    if not selected_jobid:# and not selected_date:
        raise PreventUpdate
        # return []  # Return an empty table before selection
    filtered_df = properties_df.copy()
    # Filter DataFrame based on selected PileID and Date
    if not selected_jobid is None:
        filtered_df = filtered_df[(filtered_df["JobNumber"] == selected_jobid)]
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
            time = datetime.today()
        movetime = row['MoveTime']
        try:
            movetime = datetime.strptime(movetime, '%H:%M:%S').time()
        except:
            pass
        try:
            totaltime = row['TotalTime']
            totaltime = datetime.strptime(totaltime, '%H:%M:%S').time()
        except:
            totaltime =None
            pass

        try:
            delaytime = row['DelayTime']
            delaytime = datetime.strptime(delaytime, '%H:%M:%S').time()
        except:
            delaytime = None
            pass
        movedistance = row['MoveDistance']
        try:
            movedistance = round(float(movedistance),1)
        except:
            pass
        try:
            delay = row['Delay']
        except:
            delay = None

        if not selected_date is None:
            use_date = selected_date
        else:
            use_date = datetime.today().date().strftime(format='%Y-%m-%d')

        min_depth = None
        max_strokes = None
        if not selected_jobid is None:
            # Retrieve Depth & Strokes from pile_data
            pile_data = jobid_pile_data[selected_jobid]
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
            "JobNumber": row['JobNumber'],
            "LocationID": row['LocationID'],
            "MinDepth": min_depth,
            "MaxStrokes": max_strokes,
            "OverBreak": f"{(row['OverBreak'] - 1) * 100:.0f}%",
            "PileStatus": row['PileStatus'],
            "PileCode": row['PileCode'],
            "Comments": row["Comments"],
            "DelayTime": delaytime,
            "Delay": delay,
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
@callback(
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
        filtered_df = filtered_df[filtered_df["JobNumber"] == selected_jobid]
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
@callback(
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
        filtered_df = filtered_df[filtered_df['JobNumber'] == selected_jobid]
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

                # Assign different marker styles
                if pile_code.lower() == "Production Pile".lower():  # Circle
                    if piletype == 1:
                        donut = "/assets/blue-donut.png"
                    else:
                        donut = "/assets/yellow-donut.png"
                    marker = dl.Marker(
                        position=(row["latitude"], row["longitude"]),
                        icon=dict(
                            iconUrl=donut,  # Path to your image in assets folder
                            iconSize=[30, 30]  # Size of the icon in pixels
                        ),
                        children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")]
                    )

                elif pile_code.lower() == "TEST PILE".lower():  # Square (Using a rectangle as an approximation)
                    marker = dl.Marker(
                        position=(row["latitude"], row["longitude"]),
                        icon=dict(
                            iconUrl='assets/yellow-square.png',  # Path to your image in assets folder
                            iconSize=[30, 30]  # Size of the icon in pixels
                        ),
                        children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")]
                    )

                elif pile_code.lower() == "REACTION PILE".lower():  # Octagon (Using a custom SVG marker)
                    marker = dl.Marker(
                        position=(row["latitude"], row["longitude"]),
                        icon=dict(
                            iconUrl='assets/blue-target.png',  # Path to your image in assets folder
                            iconSize=[30, 30]  # Size of the icon in pixels
                        ),
                        children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")]
                    )

                else:  # Default marker for other PileCodes Probe
                    marker = dl.Marker(
                        position=(row["latitude"], row["longitude"]),
                        icon=dict(
                            iconUrl="/assets/red-triangle.png",  # Path to your image in assets folder
                            iconSize=[30, 30]  # Size of the icon in pixels
                        ),
                        children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")]
                    )
                center = [row["latitude"], row["longitude"]]
                markers.append(marker)

                if not selected_pileid is None:  # Recenter on selected PileID
                    center = [row["latitude"], row["longitude"]]

    return markers, center,zoom_level, f"map-{center_lat}-{center_lon}-{zoom_level}"


@callback(
    Output("time_graph", "figure"),
    Output("depth_graph", "figure"),
    Output('download-pdf-btn', 'disabled'),
    Input('pilelist-table', 'selectedRows'),
    Input('window-size', 'data'),
    State("jobid-filter", "value")
    # State("jobid-filter","value"),

)
def update_combined_graph(selected_row, window_size,selected_jobid):
    if not selected_row:
        # No row selected - you might want to show all data or a default view
        return go.Figure(
            layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"}),go.Figure(
            layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"}) ,True # Dark background even if empty
    selected_row = selected_row[0]  # Get first selected row (since we're using single selection)
    selected_pileid = selected_row['PileID']
    selected_date = pd.to_datetime(selected_row['Time']).date().strftime(format='%Y-%m-%d')
    pile_data = jobid_pile_data[selected_jobid]
    pile_info = pile_data[selected_pileid][selected_date]
    try:
        diameter = float(selected_row['PileDiameter'])
    except:
        diameter = None
    fig = create_time_chart(pile_info)
    fig1 = create_depth_chart(pile_info,diameter)

    # if not window_size is None:
    #     width = window_size['width']
    #     if width < 768:  # Mobile breakpoint
    #         fig1 = create_depth_chart_small_screen(pile_info,diameter)
    #     else:
    #         fig1 = create_depth_chart(pile_info, diameter)
    # else:
    #     fig1 = create_depth_chart(pile_info, diameter)

    return fig,fig1,False

@callback(
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
    try:
        move_distance =round(move_distance,2)
    except:
        move_distance = 0
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

@callback(
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
    filtered_df = properties_df[properties_df["JobNumber"] == selected_jobid]

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
    unique_pile_count = properties_df[properties_df["JobNumber"] == selected_jobid]["PileID"].nunique()
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

@callback(
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
@callback(
    Output("collapse-map", "is_open"),
    [Input("toggle-map", "n_clicks")],
    [State("collapse-map", "is_open")]
)
def toggle_map(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@callback(
    Output("collapse-plots", "is_open"),
    [Input("toggle-plots", "n_clicks")],
    [State("collapse-plots", "is_open")]
)
def toggle_plots(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@callback(
    Output("collapse_depth_plots", "is_open"),
    [Input("toggle_depth_plots", "n_clicks")],
    [State("collapse_depth_plots", "is_open")]
)
def toggle_plots(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@callback(
    Output("collapse-views", "is_open"),
    [Input("toggle-views", "n_clicks")],
    [State("collapse-views", "is_open")]
)
def toggle_views(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

#
@callback(
    Output("collapse-pilelist", "is_open"),
    [Input("toggle-pilelist", "n_clicks")],
    [State("collapse-pilelist", "is_open")]
)
def toggle_views(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open


@callback(
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


@callback(
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
        return generate_mwd_pdf(selected_row, time_fig, depth_fig)
    except Exception as e:
        print(f"PDF generation failed: {str(e)}")
        return no_update


# ==================================================================
# ============TEST FUNCTION=========================================
# @app.callback(
#     Output("task-id", "data"),
#     Output("poll-interval", "disabled"),
#     Output("task-output", "children"),
#     Input("download-ALL-pdf-btn", "n_clicks"),
#     Input("poll-interval", "n_intervals"),
#     State("task-id", "data"),
#     prevent_initial_call=True
# )
# def manage_task(start_clicks, n_intervals, task_id):
#     ctx = callback_context
#
#     if not ctx.triggered:
#         raise dash.exceptions.PreventUpdate
#
#     triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
#
#     # Start the task
#     if triggered_id == "download-ALL-pdf-btn":
#         task = generate_numbers.apply_async(args=[2, 3])
#         return task.id, False, "Task started..."
#
#     # Poll the result
#     elif triggered_id == "poll-interval" and task_id:
#         result = AsyncResult(task_id, app=celery_app)
#         if result.ready():
#             return task_id, True, f"Task finished! Result: {result.result}"
#         else:
#             return task_id, False, "Processing..."
#
#     # Fallback
#     raise dash.exceptions.PreventUpdate

# ==================================================================
# ==================================================================
@callback(
        Output("task-id", "data"),
        Output("poll-interval", "disabled",allow_duplicate=True),
        Input("download-ALL-pdf-btn", "n_clicks"),
        State('pilelist-table', 'rowData'),
        State("jobid-filter", "value"),
        prevent_initial_call=True,

    )
def start_task(n_clicks, all_rows,selected_jobid):
    if not n_clicks or not all_rows:
        raise PreventUpdate
    try:
        print('Entering the task')
        pile_data = jobid_pile_data[selected_jobid]
        task = generate_all_pdfs_task.delay(all_rows, pile_data)
        return task.id, False
    except Exception as e:
        return None,False

# print(">>> Calling task")
#     task = generate_all_pdfs_task.delay([{"PileID": 1, "Time": "2024-01-01"}], {"1": {"2024-01-01": {}}})
#     print(">>> Task ID:", task.id)


@callback(
    Output('task-status', 'children'),
    Output('download-ALL-pdf', 'data'),
    Output("poll-interval", "disabled"),  # Make sure this matches your Interval component id
    Input("poll-interval", "n_intervals"),
    State("task-id", "data"),
    prevent_initial_call=True
)
def poll_status(n, task_id):
    if not task_id:
        raise PreventUpdate

    res = AsyncResult(task_id, app=celery_app)

    if res.ready():
        if res.successful():
            filename = res.result
            filepath = os.path.join(root_path, "instance", "tmp", filename)
            print(filepath)  # This should only print once now
            if not os.path.exists(filepath):
                print(f"❌ File not found at: {filepath}")
                return "❌ File not found", None, True
            return "✅ Done", dcc.send_file(filepath), True
        else:
            return "❌ Failed", None, True
    else:
        return "⏳ In progress", None, False