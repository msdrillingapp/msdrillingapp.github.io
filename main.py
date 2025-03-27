import dash
import pandas as pd
import dash_leaflet as dl
import json
from dash import dcc, html, Output, Input, ctx, dash_table,callback_context,MATCH, State,ClientsideFunction
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from utility_funtions import filter_none,load_geojson_data,get_plotting_zoom_level_and_center_coordinates_from_lonlat_tuples


#####################
# Empty row
def get_emptyrow(h='45px'):
    """This returns an empty row of a defined height"""

    emptyrow = html.Div([
        html.Div([
            html.Br()
        ], className = 'col-12')
    ],
    className = 'row',
    style = {'height' : h})

    return emptyrow

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
groups_list.insert(0, 'Edit')
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
app = dash.Dash(__name__, external_stylesheets=["/assets/style.css"],suppress_callback_exceptions=True)
app.title = 'MS Drill Tracker'
server = app.server

app.layout = html.Div([
    html.Div([
        html.H1(title_text, style={'textAlign': 'left', 'color': 'white', 'flex': '1'}),
        html.Img(src="/assets/MSB.logo.JPG",
                 style={'height': '80px', 'position': 'absolute', 'top': '10px', 'right': '20px'}
)
    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),

    # FILTERS ===================================================================
    html.Div([
        dcc.Dropdown(
                id="jobid-filter",
                options=[{"label": str(r), "value": str(r)} for r in properties_df["JobID"].dropna().unique()],
                placeholder="Filter by JobID",
                style={'width': '250px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            ),

        dcc.Dropdown(
            id="date-filter",
            options=[{"label": d, "value": d} for d in sorted(properties_df["date"].unique())],
            placeholder="Select a Date",
            style={'width': '250px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
            className="dark-dropdown"
        ),
        dcc.Dropdown(
                id="rigid-filter",
                options=[{"label": str(r), "value": str(r)} for r in properties_df["RigID"].dropna().unique()],
                placeholder="Filter by RigID",
                style={'width': '250px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            ),
        dcc.Dropdown(
            id="pileid-filter",
            options=[{"label": str(p), "value": str(p)} for p in properties_df["PileID"].dropna().unique()],
            placeholder="Filter by PileID",
            style={'width': '250px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
            className="dark-dropdown"
        ),

    ], style={'marginBottom': '10px', 'display': 'flex', 'justifyContent': 'center'}),

    # html.Br(),
    html.Div([
        dcc.Dropdown(
            id="pilecode-filter",
            options=[{"label": str(r), "value": str(r)} for r in properties_df["PileCode"].dropna().unique()],
            placeholder="Filter by PileCode",
            style={'width': '250px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
            className="dark-dropdown"
        ),
        dcc.Dropdown(
            id="productcode-filter",
            options=[{"label": str(r), "value": str(r)} for r in properties_df["ProductCode"].dropna().unique()],
            placeholder="Filter by ProductCode",
            style={'width': '250px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
            className="dark-dropdown"
        ),
        #
        dcc.Dropdown(
            id="piletype-filter",
            options=[{"label": str(r), "value": str(r)} for r in properties_df["PileType"].dropna().unique()],
            placeholder="Filter by PileType",
            style={'width': '250px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
            className="dark-dropdown"
        ),
        dcc.Dropdown(
            id="pilestatus-filter",
            options=[{"label": str(r), "value": str(r)} for r in properties_df["PileStatus"].dropna().unique()],
            placeholder="Filter by PileStatus",
            style={'width': '250px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
            className="dark-dropdown"
        ),

    ], style={'marginBottom': '20px', 'display': 'flex', 'justifyContent': 'center'}),

    # html.Button(
    #     "Reset Filters", id="reset-button", n_clicks=0, style={
    #         'marginTop': '10px', 'padding': '10px 15px', 'fontSize': '16px',
    #         'cursor': 'pointer', 'backgroundColor': '#dc3545', 'color': 'white',
    #         'border': 'none', 'borderRadius': '5px'
    #     }
    # ),
    # =============================MAP=================================================
    dl.Map(id="map", center=map_center, zoom=zoom_level,zoomControl=True,  children=[
        dl.TileLayer(),
        dl.LayerGroup(markers,id="map-markers"),

    ], style={'width': '100%', 'height': '400px','align':'center','marginleft': '10px', 'display': 'flex', 'justifyContent': 'center'}),
    html.Br(),

    # ===============================================
    html.Div([
        # Statistics Info Cards
        html.Div(id="pile-summary-cards", style={
            'display': 'flex', 'justifyContent': 'space-around', 'alignItems': 'center',
            'backgroundColor': '#1f4068', 'color': 'white', 'padding': '10px',
            'borderRadius': '5px', 'marginTop': '10px'
        }),
    ]),
# ===============================================
    # Table & Chart Side by Side
    html.Div([

        # Graph
        dcc.Graph(id="strokes-depth-time-graph"),
            # ]),
        # Table (Right)

        html.Div([
            html.Label("Select PileID:", style={'color': 'white'}),
            dcc.Dropdown(
                id="pileid-filter-top",
                placeholder="Filter by PileID",
                style={'width': '200px', 'marginBottom': '10px', 'marginRight': '10px'},
                className="dark-dropdown"
            ),
            # Group Filter Dropdown (Above Table)
            html.Label("Filter by Group:", style={'color': 'white'}),
            dcc.Dropdown(
                id="group-filter",
                options=[{"label": g, "value": g} for g in groups_list],
                placeholder="Filter by Group",
                style={'width': '200px', 'marginBottom': '10px', 'marginRight': '10px'},
                className="dark-dropdown"
             ),
            # Table
            dash_table.DataTable(
                id="filtered-table",
                columns=[
                    {"name": "Field", "id": "Field", "editable": False},
                    {"name": "Value", "id": "Value", "editable": True, "presentation": "input"}
                ],
                data=[],  # Start with an empty table
                # dropdown_conditional=[],  # Will be updated dynamically
                filter_action="native",
                # sort_action="native",
                sort_action=None,  # ❌ Disable sorting
                page_size=10,
                style_table={
                    'overflowX': 'auto',
                    'overflowY': 'visible',  # Allow dropdown to expand outside the table
                    'width': '75%',
                    'margin': 'auto',
                    'border': '2px solid white',
                    'position': 'relative'  # Ensure the dropdown can break out of container
                },

                style_cell={
                    'textAlign': 'left',
                    'color': 'white',
                    'backgroundColor': '#193153',
                    'border': '1px solid white',  # Add borders to each cell
                    'padding': '8px'
                },
                style_header={
                    'fontWeight': 'bold',
                    'backgroundColor': '#1f4068',
                    'color': 'white',
                    'border': '2px solid white'  # Add border to the header
                },
                style_data_conditional=[
                    {
                        "if": {"filter_query": '{Field} = "Overbreak"'},  # Target Overbreak field
                        "backgroundColor": "#808080",  # Grey out
                        "color": "white",
                    } ],
                style_data={
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'minHeight': '50px'  # Adjust row height to fit the dropdown
                }
            ),
            html.Br(),
            html.Div(
                id="edit-options-container",
                children=[
                    html.Label("Delay",id='delay-label', style={"color": "white", "fontWeight": "bold", "marginBottom": "5px"}),
                    dcc.Dropdown(
                        id="edit-options",
                        options=[
                            {"label": "Waiting on Concrete", "value": "Waiting on Concrete"},
                            {"label": "Site access", "value": "Site access"},
                            {"label": "Layout", "value": "Layout"},
                            {"label": "Enter free text", "value": "free_text"}
                        ],
                        placeholder="Select an option",
                        style={"display": "none", "width": "300px", "padding": "5px","backgroundColor": "#1f4068", "color": "white"},
                        className="dark-dropdown"
                    ),
                    dcc.Input(
                        id="free-text-input",
                        type="text",
                        placeholder="Enter text",
                        style={"display": "none", "width": "300px", "padding": "5px","backgroundColor": "#1f4068", "color": "white" }  # Increased width
                    )
                ]),
            # Save Button
            html.Button("Approve Status", id="save-button", n_clicks=0, style={
                'marginTop': '10px', 'padding': '10px 15px', 'fontSize': '16px',
                'cursor': 'pointer', 'backgroundColor': '#28a745', 'color': 'white',
                'border': 'none', 'borderRadius': '5px'
            }),

            # Save Confirmation Message
            html.Div(id="save-message", style={'marginTop': '10px', 'color': 'white'}),


        ],style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'}),


    ], style={'display': 'flex', 'gap': '20px', 'justifyContent': 'center', 'padding': '20px'}),

    # Scroll to Top Button
    html.Button("⬆ Scroll to Top", id="scroll-top-button", n_clicks=0, style={
        'position': 'fixed', 'bottom': '20px', 'right': '20px', 'zIndex': '1000',
        'padding': '10px 15px', 'fontSize': '16px', 'cursor': 'pointer',
        'backgroundColor': '#1f4068', 'color': 'white', 'border': 'none',
        'borderRadius': '5px'
    })

], style={'backgroundColor': '#193153', 'height': '300vh', 'padding': '20px', 'position': 'relative'})

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
    Output("filtered-table", "data"),
    [Input("pileid-filter", "value"),
     Input("date-filter", "value"),
     Input("group-filter", "value")],prevent_initial_call=True,
)
def update_table(selected_pileid, selected_date, selected_group):
    if not selected_pileid or not selected_date:
        return []  # Return an empty table before selection
    filtered_df = merged_df.copy()
    # Filter DataFrame based on selected PileID and Date
    filtered_df = filtered_df[(filtered_df["PileID"] == selected_pileid) & (filtered_df["date"] == selected_date)]

    # Custom Order for "Edit" Group
    custom_order = [
        "PileID", "LocationID", "PileLength", "MaxStroke",
        "PumpID", "PumpCalibration", "PileStatus","PileCode","WorkingGrade", "Comments", "Delay"
    ]
    # "ProductCode""OverBreak",
    if selected_group:
        filtered_df = filtered_df[filtered_df["Group"] == selected_group]

    if selected_group == "Edit":
        # Reorder fields based on custom_order, keeping other fields at the end
        sorted_fields = sorted(filtered_df["Field"].unique(), key=lambda x: custom_order.index(x) if x in custom_order else len(custom_order))
        filtered_df = filtered_df.set_index("Field").loc[sorted_fields].reset_index()
        # tmp = pd.DataFrame([selected_pileid,selected_group,'PileID',selected_pileid,1,1,selected_date],columns=filtered_df.columns)
        new_row = ['PileID',selected_pileid,selected_group,selected_pileid,filtered_df.loc[1,'latitude'],filtered_df.loc[1,'longitude'],selected_date]
        filtered_df = pd.concat([pd.DataFrame([new_row], columns=filtered_df.columns), filtered_df]).reset_index(drop=True)
        # Add "Edited Value" column
        # filtered_df["Original Value"] = filtered_df["Value"]
        filtered_df["Edited Value"] = filtered_df["Value"]  # User edits this column
        out = filtered_df[["Field", "Value", "Edited Value"]].to_dict("records")
        out_dict = {item['Field']: item['Value'] for item in out}

        # # Modify OverBreak if it exists
        # if 'OverBreak' in out_dict:
        #     out_dict['OverBreak'] = f"{float(out_dict['OverBreak']) * 100:.2f}%"
        #
        # # Convert back to list of dictionaries
        # out = [{'Field': k, 'Value': v,'Edited Value':v} for k, v in out_dict.items()]
        # return out

    out = filtered_df[["Field", "Value"]].to_dict("records")

    out_dict = {item['Field']: item['Value'] for item in out}

    # Modify OverBreak if it exists
    if 'OverBreak' in out_dict:
        out_dict['OverBreak'] = f"{float(out_dict['OverBreak']) * 100:.2f}%"

    # Convert back to list of dictionaries
    out = [{'Field': k, 'Value': v} for k, v in out_dict.items()]

    return out


# =================================================================================================
# Callback to update dropdown options based on selections
@app.callback(
    [
        Output("date-filter", "options"),
        Output("rigid-filter", "options"),
        Output("pileid-filter", "options"),
        Output("pileid-filter-top", "options"),
        Output("pilecode-filter", "options"),
        Output("pilestatus-filter", "options"),
        Output("piletype-filter", "options"),
        Output("productcode-filter", "options"),

        Output("date-filter", "value"),
        Output("rigid-filter", "value"),
        Output("pileid-filter", "value"),
        Output("pileid-filter-top", "value"),
        Output("pilecode-filter", "value"),
        Output("pilestatus-filter", "value"),
        Output("piletype-filter", "value"),
        Output("productcode-filter", "value"),
    ],
    [
        Input("jobid-filter", "value"),
        Input("date-filter", "value"),
        Input("rigid-filter", "value"),
        Input("pileid-filter", "value"),
        Input("pileid-filter-top", "value"),
        Input("pilecode-filter", "value"),
        Input("pilestatus-filter", "value"),
        Input("piletype-filter", "value"),
        Input("productcode-filter", "value"),
    ],
    [
        State("date-filter", "value"),
        State("rigid-filter", "value"),
        State("pileid-filter", "value"),
        State("pileid-filter-top", "value"),
        State("pilecode-filter", "value"),
        State("pilestatus-filter", "value"),
        State("piletype-filter", "value"),
        State("productcode-filter", "value"),
    ], allow_duplicate=True,prevent_initial_call=True,
)
def update_filter_options(selected_jobid, selected_date, selected_rigid, selected_pileid,selected_pileid_top,
                          selected_pilecode, selected_pilestatus, selected_piletype, selected_productcode,
                          prev_date, prev_rigid, prev_pileid, prev_pileid_top, prev_pilecode, prev_pilestatus, prev_piletype,
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
        return (date_options, rigid_options, pileid_options, pileid_options, pilecode_options, pilestatus_options,
                piletype_options, productcode_options,
                None, None, None, None, None, None, None, None)  # Reset everything

    # Sync pileid-filter and pileid-filter-top
    if triggered_id == "pileid-filter":
        return (date_options, rigid_options, pileid_options, pileid_options, pilecode_options, pilestatus_options,
                piletype_options, productcode_options,
                prev_date, prev_rigid, selected_pileid, selected_pileid, prev_pilecode, prev_pilestatus, prev_piletype,
                prev_productcode)

    if triggered_id == "pileid-filter-top":
        return (date_options, rigid_options, pileid_options, pileid_options, pilecode_options, pilestatus_options,
                piletype_options, productcode_options,
                prev_date, prev_rigid, selected_pileid_top, selected_pileid_top, prev_pilecode, prev_pilestatus,
                prev_piletype, prev_productcode)

    # Otherwise, **keep previous selections**
    return (date_options, rigid_options, pileid_options,pileid_options, pilecode_options, pilestatus_options, piletype_options,
            productcode_options,
            prev_date, prev_rigid, prev_pileid, prev_pileid_top, prev_pilecode, prev_pilestatus, prev_piletype, prev_productcode)




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

                # Assign different marker styles
                if pile_code.lower() == "Production Pile".lower():  # Circle
                    marker = dl.CircleMarker(
                        center=(row["latitude"], row["longitude"]),
                        radius=5, color="blue", fill=True,
                        children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")]
                    )

                elif pile_code.lower() == "TEST PILE".lower():  # Square (Using a rectangle as an approximation)
                    marker = dl.Rectangle(
                        bounds=[(row["latitude"] - 0.0001, row["longitude"] - 0.0001),
                                (row["latitude"] + 0.0001, row["longitude"] + 0.0001)],
                        color="green", fill=True,
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
                        children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")]
                    )
                center = [row["latitude"], row["longitude"]]
                markers.append(marker)

                if not selected_pileid is None:  # Recenter on selected PileID
                    center = [row["latitude"], row["longitude"]]

    return markers, center,zoom_level, f"map-{center_lat}-{center_lon}-{zoom_level}"

# Callback to track edited values and highlight changes
@app.callback(
    Output("filtered-table", "style_data_conditional"),
    [Input("filtered-table", "data_previous"), Input("group-filter", "value")],
    State("filtered-table", "data"),prevent_initial_call=True
)
def highlight_changes(prev_data, selected_group, current_data):
    if not prev_data or not selected_group:
        return []

    styles = []
    changed_values[selected_group] = set()
    for i, (prev_row, curr_row) in enumerate(zip(prev_data, current_data)):
        if prev_row["Value"] != curr_row["Value"] and selected_group=='Edit':
            changed_values[selected_group].add(i)

    styles.extend([
        {"if": {"row_index": i, "column_id": "Value"}, "color": "#ffcc00", "fontWeight": "bold"}
        for i in changed_values.get(selected_group, [])
    ])

    return styles



# Callback to update the combined graph
@app.callback(
    Output("strokes-depth-time-graph", "figure"),
    [Input("pileid-filter", "value"), Input("date-filter", "value")],
    State("jobid-filter","value")
)
def update_combined_graph(selected_pileid, selected_date,selected_jobid):
    if not selected_pileid or selected_pileid not in pile_data or selected_date not in pile_data[selected_pileid]:
        return go.Figure(
            layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"}) # Dark background even if empty

    pile_info = pile_data[selected_pileid][selected_date]

    # Create figure with two y-axes
    fig = px.line(title=f"JobID {selected_jobid} - PileID {selected_pileid} on {selected_date}")

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
        yaxis=dict(title="Depth", side="left", showgrid=False),
        yaxis2=dict(title="Strokes", overlaying="y", side="right", showgrid=False),
        plot_bgcolor="#193153",
        paper_bgcolor="#193153",
        font=dict(color="white")
    )

    return fig

@app.callback(
    Output("pile-summary-cards", "children"),
    [Input("pileid-filter", "value"), Input("jobid-filter", "value")]
)
def update_summary_cards(selected_pileid, selected_jobid):
    if not selected_pileid or not selected_jobid:
        return html.Div("Select a PileID to view statistics.", style={'color': 'white', 'textAlign': 'center'})

    # Filter data for the selected PileID
    filtered_df = properties_df[properties_df["PileID"] == selected_pileid]

    # Extract statistics
    move_time = filtered_df["MoveTime"].iloc[0] if "MoveTime" in filtered_df.columns else "N/A"
    move_distance = filtered_df["MoveDistance"].iloc[0] if "MoveDistance" in filtered_df.columns else "N/A"
    delay_time = filtered_df["DelayTime"].iloc[0] if "DelayTime" in filtered_df.columns else "N/A"
    overbreak = f"{float(filtered_df['OverBreak'].iloc[0]) * 100:.2f}%" if "OverBreak" in filtered_df.columns else "N/A"
    # f"{float(filtered_df["OverBreak"].iloc[0]) * 100:.2f}%"
    # Count distinct PileIDs for the selected JobID
    unique_pile_count = properties_df[properties_df["JobID"] == selected_jobid]["PileID"].nunique()

    # Create info cards
    return [
        html.Div([html.P("⏳ Move Time"), html.H4(move_time)], style={'textAlign': 'center', 'padding': '10px'}),
        html.Div([html.P("📏 Move Distance"), html.H4(move_distance)], style={'textAlign': 'center', 'padding': '10px'}),
        html.Div([html.P("⏰ Delay Time"), html.H4(delay_time)], style={'textAlign': 'center', 'padding': '10px'}),
        html.Div([html.P("🚧 OverBreak"), html.H4(overbreak)], style={'textAlign': 'center', 'padding': '10px'}),
        html.Div([html.P("🔢 Piles in Job"), html.H4(unique_pile_count)], style={'textAlign': 'center', 'padding': '10px'})
    ]


@app.callback(
    Output("save-message", "children"),
    Input("save-button", "n_clicks"),
    State("filtered-table", "data"),
    State("group-filter", "value"),prevent_initial_call=True,
)
def save_changes(n_clicks, table_data, selected_group):
    if n_clicks > 0 and selected_group == "Edit":
        # Convert table data to a DataFrame
        df_edited = pd.DataFrame(table_data)

        # Save only if there is data
        if not df_edited.empty:
            df_edited.to_csv(os.path.join(file_path,"edited_data.csv"), index=False)  # Save to CSV file
            return "Changes saved successfully!"

    return ""


@app.callback(
    Output("filtered-table", "columns"),
    [Input("group-filter", "value")],
    prevent_initial_call=True
)
# , Output("filtered-table", "dropdown_conditional")
def update_columns(selected_group):
    if selected_group == "Edit":
        columns = [
            {"name": "Field", "id": "Field", "editable": False},
            {"name": "Value", "id": "Value", "editable": False},
            {"name": "Edited Value", "id": "Edited Value", "editable": True, "presentation": "input"}
        ]

    else:
        columns = [
            {"name": "Field", "id": "Field", "editable": False},
            {"name": "Value", "id": "Value", "editable": False}
        ]


    return columns#, dropdown_conditional
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

@app.callback(
    [Output("delay-label", "style"),
     Output("edit-options", "style"),
     Output("edit-options-container", "style"),Output("free-text-input", "style")],
    [Input("group-filter", "value"), Input("edit-options", "value")]  # Assuming this is the dropdown that selects the group
)
def toggle_edit_dropdown(selected_group, selected_option):
    if selected_group == "Edit":
        visible_style = {"color": "white", "fontWeight": "bold", "marginBottom": "5px"}  # Show label
        dropdown_style = {"display": "block", "width": "300px", "padding": "5px", "backgroundColor": "#1f4068","color": "white"}  # Show dropdown
        input_style = {"display": "none", "width": "300px", "padding": "5px","backgroundColor": "#1f4068", "color": "white"}  # Hide input initially  # Show dropdown
        container_style = {"display": "flex", "flexDirection": "column", "alignItems": "flex-start"}  # Show container
        if selected_option == "free_text":
                input_style = {"display": "block", "width": "300px", "padding": "5px","backgroundColor": "#1f4068", "color": "white"}  # Show input field
                dropdown_style = {"display": "none", "width": "300px", "padding": "5px","backgroundColor": "#1f4068", "color": "white"}  # Hide dropdown
        return visible_style, dropdown_style, container_style,input_style
    else:
        hidden_style = {"display": "none"}
        return hidden_style, hidden_style, hidden_style ,hidden_style # Hide everything

    return visible_style, dropdown_style, container_style,input_style

# Run the app
if __name__ == "__main__":
    # app.run_server(debug=True)
    app.run_server(debug=False)

#
