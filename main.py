import dash
import pandas as pd
import dash_leaflet as dl
import json
from dash import dcc, html, Output, Input, ctx, dash_table,callback_context,MATCH, State,ClientsideFunction
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os


def filter_none(lst):
    return filter(lambda x: not x is None, lst)

# Folder containing GeoJSON files
file_path = os.path.join(os.getcwd(), "assets",)
geojson_folder = os.path.join(file_path,'data')
# # Create a dictionary to map Field to Group
groups_df = pd.read_csv(os.path.join(file_path,'Groups.csv'))
groups_df = groups_df.explode("Group").reset_index(drop=True)
title_text = "Morris-Shea Drilling App"

# Function to load all GeoJSON files dynamically
def load_geojson_data():
    all_data = []
    pile_data = {}
    markers = []
    latitudes = []
    longitudes =[]
    for filename in os.listdir(geojson_folder):
        if filename.endswith(".json"):
            # file_date = filename.replace("header", "").replace(".json", "").strip()  # Extract date from filename
            file_path = os.path.join(geojson_folder, filename)

            with open(file_path, "r", encoding = "utf-8") as f:
                geojson_data = json.load(f)

            features = geojson_data.get("features", [])

            for feature in features:
                properties = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                coords = geometry.get("coordinates", [])

                if coords and len(coords) >= 2:
                    lat, lon = coords[:2]  # Ensure correct coordinate order
                    properties["latitude"] = lat
                    properties["longitude"] = lon
                    latitudes.append(lat)
                    longitudes.append(lon)
                    try:
                        date= pd.to_datetime(properties['Time']).date().strftime(format='%Y-%m-%d')
                    except:
                        date = 'NA'
                    properties["date"] = date # Store the date from the filename
                    if not lat is None and not lon is None:
                        markers.append(dl.CircleMarker(
                            center=[lat, lon],
                            radius=8,  # Bigger marker
                            color="yellow",
                            fill=True,
                            fillColor="yellow",
                            fillOpacity=0.7,
                            # children=dl.Popup(feature.get("properties", {}).get("JobName", "Unknown"))
                            children=dl.Popup("PileID: " + feature.get("properties", {}).get("PileID", "Unknown"))
                        ))
                    # Store time-series data separately for graph plotting
                    pile_id = properties.get("PileID")
                    if pile_id and "Data" in properties:
                        pile_data.setdefault(pile_id, {})[properties['date']] = {
                            "Time": properties["Data"].get("Time", []),
                            "Strokes": properties["Data"].get("Strokes", []),
                            "Depth": properties["Data"].get("Depth", [])
                        }

                    all_data.append(properties)

    return pd.DataFrame(all_data), pile_data,latitudes,longitudes,markers


# Load all datasets
properties_df, pile_data,latitudes,longitudes,markers = load_geojson_data()

properties_df.drop(columns=['Data','UID','FileName'],inplace=True)

# Melt the dataframe so each property is mapped to a Field and PileID
melted_df = properties_df.melt(id_vars=["PileID","latitude", "longitude", "date"], var_name="Field", value_name="Value")
# "JobID","RigID", "PileCode","ProductCode","PileStatus" ,"PileType"
# Convert non-string values to strings to avoid DataTable errors
melted_df["Value"] = melted_df["Value"].astype(str)

# Merge with Groups.csv
merged_df = melted_df.merge(groups_df, on="Field", how="left")
merged_df["Group"].fillna("Undefined", inplace=True)  # Ensure Group is always a string
# Keep only relevant columns
filtered_columns = ["PileID", "Group", "Field", "Value", "latitude", "longitude", "date"]
# "JobID","RigID", "PileCode","ProductCode","PileStatus","PileType"
merged_df = merged_df[filtered_columns]
groups_list = list(merged_df["Group"].dropna().unique())
groups_list.remove('Edit')
groups_list.insert(0, 'Edit')
# Track changed values
# changed_values = set()
changed_values ={}

# Calculate map center and zoom
if latitudes and longitudes:
    # lat = [float(item) for var in latitudes for item in latitudes if item != 'None']
    center_lat = np.nanmean([float(item) for var in latitudes for item in latitudes if not item is None])
    center_lon = np.nanmean([float(item) for var in longitudes for item in longitudes if not item is None])
    map_center = [center_lat, center_lon]
    zoom_level = 10  # Adjust zoom for a closer view
else:
    map_center = [40, -100]
    zoom_level = 4

# Create Dash app
app = dash.Dash(__name__, external_stylesheets=["/assets/style.css"])
app.title = 'MS Drill Tracker'
server = app.server

app.layout = html.Div([
    html.Div([
        html.H1(title_text, style={'textAlign': 'left', 'color': 'white', 'flex': '1'}),
        html.Img(src="/assets/MSB.logo.JPG",
                 style={'height': '80px', 'position': 'absolute', 'top': '10px', 'right': '20px'}
        # style = {'height': '100px', 'position': 'absolute', 'top': '10px', 'right': '20px'}
        # style = {'width': '100%', 'height': '100%'}
)
    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),

    # FILTERS ===================================================================
    html.Div([
        dcc.Dropdown(
                id="jobid-filter",
                options=[{"label": str(r), "value": str(r)} for r in properties_df["JobID"].dropna().unique()],
                placeholder="Filter by JobID",
                # style={'width': '250px', 'marginBottom': '10px','backgroundColor': '#193153', 'color': 'white'}
                # style={'width': '250px', 'marginBottom': '10px'},
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
                # style={'width': '250px', 'marginBottom': '10px','backgroundColor': '#193153', 'color': 'white'}
                # style={'width': '250px', 'marginBottom': '10px'},
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
    #  MAP ===============================================
    # # Button to enable box zoom
    # html.Button("Select Area to Zoom", id="zoom-button", n_clicks=0, style={
    #     'position': 'absolute', 'top': '10px', 'left': '10px', 'zIndex': '1000'
    # }),
    dl.Map(id="map", center=map_center, zoom=zoom_level,zoomControl=True,  children=[
        dl.TileLayer(),
        dl.LayerGroup(markers,id="map-markers"),

    ], style={'width': '100%', 'height': '500px'}),
    html.Br(),

    # ===============================================

    # Table & Chart Side by Side
    html.Div([

        # Graph
        dcc.Graph(id="strokes-depth-time-graph"),
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
                filter_action="native",
                sort_action="native",
                page_size=10,
                # style_table={'overflowX': 'auto', 'width': '50%', 'backgroundColor': '#193153'},
                style_table={'overflowX': 'auto', 'width': '75%', 'margin': 'auto', 'border': '2px solid white'},
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
                    }
    ]
            ),# Save Button
            html.Button("Save Changes", id="save-button", n_clicks=0, style={
                'marginTop': '10px', 'padding': '10px 15px', 'fontSize': '16px',
                'cursor': 'pointer', 'backgroundColor': '#28a745', 'color': 'white',
                'border': 'none', 'borderRadius': '5px'
            }),

            # Save Confirmation Message
            html.Div(id="save-message", style={'marginTop': '10px', 'color': 'white'})
        ]),


    ], style={'display': 'flex', 'gap': '20px', 'justifyContent': 'center', 'padding': '20px'}),

    # Scroll to Top Button
    html.Button("⬆ Scroll to Top", id="scroll-top-button", n_clicks=0, style={
        'position': 'fixed', 'bottom': '20px', 'right': '20px', 'zIndex': '1000',
        'padding': '10px 15px', 'fontSize': '16px', 'cursor': 'pointer',
        'backgroundColor': '#1f4068', 'color': 'white', 'border': 'none',
        'borderRadius': '5px'
    })

], style={'backgroundColor': '#193153', 'height': '250vh', 'padding': '20px', 'position': 'relative'})



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
     Input("group-filter", "value")]
)
def update_table(selected_pileid, selected_date, selected_group):
    if not selected_pileid or not selected_date:
        return []  # Return an empty table before selection
    filtered_df = merged_df.copy()
    # Filter DataFrame based on selected PileID and Date
    filtered_df = filtered_df[(filtered_df["PileID"] == selected_pileid) & (filtered_df["date"] == selected_date)]

    # Custom Order for "Edit" Group
    custom_order = [
        "PileID", "LocationID", "PileLength", "MaxStroke", "OverBreak",
        "PumpID", "PumpCalibration", "PileStatus","ProductCode","PileCode","WorkingGrade", "Comments", "Notes"
    ]
    if selected_group:
        filtered_df = filtered_df[filtered_df["Group"] == selected_group]

    if selected_group == "Edit":
        # Reorder fields based on custom_order, keeping other fields at the end
        sorted_fields = sorted(filtered_df["Field"].unique(), key=lambda x: custom_order.index(x) if x in custom_order else len(custom_order))
        filtered_df = filtered_df.set_index("Field").loc[sorted_fields].reset_index()
        # tmp = pd.DataFrame([selected_pileid,selected_group,'PileID',selected_pileid,1,1,selected_date],columns=filtered_df.columns)
        filtered_df.loc[0] = ['PileID',selected_pileid,selected_group,selected_pileid,filtered_df.loc[1,'latitude'],filtered_df.loc[1,'longitude'],selected_date]
        # Add "Edited Value" column
        # filtered_df["Original Value"] = filtered_df["Value"]
        filtered_df["Edited Value"] = filtered_df["Value"]  # User edits this column
        out = filtered_df[["Field", "Value", "Edited Value"]].to_dict("records")
        out_dict = {item['Field']: item['Value'] for item in out}

        # Modify OverBreak if it exists
        if 'OverBreak' in out_dict:
            out_dict['OverBreak'] = f"{float(out_dict['OverBreak']) * 100:.2f}%"

        # Convert back to list of dictionaries
        out = [{'Field': k, 'Value': v,'Edited Value':v} for k, v in out_dict.items()]
        return out

    out = filtered_df[["Field", "Value"]].to_dict("records")

    out_dict = {item['Field']: item['Value'] for item in out}

    # Modify OverBreak if it exists
    if 'OverBreak' in out_dict:
        out_dict['OverBreak'] = f"{float(out_dict['OverBreak']) * 100:.2f}%"

    # Convert back to list of dictionaries
    out = [{'Field': k, 'Value': v} for k, v in out_dict.items()]

    return out

# Callback to update PileID dropdown based on selected date
@app.callback(
    [Output("pileid-filter", "options"), Output("pileid-filter-top", "options")],
    [Input("date-filter", "value"),
     Input("rigid-filter", "value"),
     Input('jobid-filter',"value"),
     Input('pilecode-filter',"value"),
     Input('pilestatus-filter',"value"),
     Input('piletype-filter',"value"),
     Input('productcode-filter',"value")]
)
def update_pileid_options(selected_date,selected_rigid,selected_jobid,
                          selected_pilecode,selected_pilestatus,selected_piletype,selected_productcode):
    if not selected_date and not selected_rigid and not selected_jobid and not selected_pilecode and not selected_pilestatus and not selected_piletype and not selected_productcode:
        return [],[]
    filtered_df = properties_df.copy()
    if selected_date:
        filtered_df = filtered_df[filtered_df["date"] == selected_date]
    if selected_rigid:
        filtered_df = filtered_df[filtered_df['RigID']==selected_rigid]
    if selected_jobid:
        filtered_df = filtered_df[filtered_df['JobID'] == selected_jobid]
    if selected_pilecode:
        filtered_df = filtered_df[filtered_df['PileCode'] == selected_pilecode]
    if selected_pilestatus:
        filtered_df = filtered_df[filtered_df['PileStatus'] == selected_pilestatus]
    if selected_piletype:
        filtered_df = filtered_df[filtered_df['PileType'] == selected_piletype]
    if selected_productcode:
        filtered_df= filtered_df[filtered_df['ProductCode'] == selected_productcode]

    return [{"label": str(p), "value": str(p)} for p in filtered_df["PileID"].dropna().unique()],[{"label": str(p), "value": str(p)} for p in filtered_df["PileID"].dropna().unique()]

@app.callback(
    Output("rigid-filter", "options"),
    [Input("date-filter", "value"),
     Input('jobid-filter',"value"),
     Input('pilecode-filter',"value"),
     Input('pilestatus-filter', "value"),
     Input('piletype-filter', "value"),
     Input('productcode-filter', "value")]
)
def update_rigid_options(selected_date,selected_jobid,selected_pilecode,selected_pilestatus,selected_piletype,selected_productcode):
    if not selected_date and not selected_jobid and not selected_pilecode and not selected_pilestatus and not selected_piletype and not selected_productcode:
        return []
    filtered_df = properties_df.copy()
    if selected_date:
        filtered_df = properties_df[properties_df["date"] == selected_date]
    if selected_jobid:
        filtered_df = filtered_df[filtered_df['JobID'] == selected_jobid]
    if selected_pilecode:
        filtered_df = filtered_df[filtered_df['PileCode'] == selected_pilecode]
    if selected_pilestatus:
        filtered_df = filtered_df[filtered_df['PileStatus'] == selected_pilestatus]
    if selected_piletype:
        filtered_df = filtered_df[filtered_df['PileType'] == selected_piletype]
    if selected_productcode:
        filtered_df= filtered_df[filtered_df['ProductCode'] == selected_productcode]

    return [{"label": str(p), "value": str(p)} for p in filtered_df["RigID"].dropna().unique()]

# Callback to update date based on JobID
@app.callback(
    Output("date-filter", "options"),
    [Input("jobid-filter", "value"),]
)
def update_date_options(selected_jobid):

    filtered_df = properties_df.copy()

    if not selected_jobid is None:
        filtered_df = filtered_df[filtered_df['JobID'] == selected_jobid]

    out = list(filtered_df["date"].dropna().unique())
    out = [pd.to_datetime(x).date() for x in out]
    out.sort()
    out = [x.strftime(format='%Y-%m-%d') for x in out]
    return [{"label": str(p), "value": str(p)} for p in out]


# Callback to update map markers and recenter the map
@app.callback(
    [Output("map-markers", "children"), Output("map", "center"),Output('map','zoom')],
    [Input("date-filter", "value"),
     Input("rigid-filter", "value"),
     Input("pileid-filter", "value"),
     Input('jobid-filter', "value"),
     Input('pilecode-filter', "value"),
     Input('pilestatus-filter', "value"),
     Input('piletype-filter', "value"),
     Input('productcode-filter', "value")
     ]
)
def update_map_markers(selected_date, selected_rigid, selected_pileid,selected_jobid,selected_pilecode,selected_pilestatus,selected_piletype,selected_productcode):
    filtered_df = properties_df.copy()

    center = [np.nanmean(list(filter_none(properties_df["latitude"]))), np.nanmean(list(filter_none(properties_df["longitude"])))]
    zoom_level = 8
    # Apply filters
    if selected_date:
        filtered_df = filtered_df[filtered_df["date"] == selected_date]
    if selected_rigid:
        filtered_df = filtered_df[filtered_df["RigID"] == selected_rigid]
        zoom_level = 20
    if selected_pileid:
        filtered_df = filtered_df[filtered_df["PileID"] == selected_pileid]
        zoom_level =35
    if selected_jobid:
        filtered_df = filtered_df[filtered_df['JobID'] == selected_jobid]
        zoom_level = 15
    if selected_pilecode:
        filtered_df = filtered_df[filtered_df['PileCode'] == selected_pilecode]
    if selected_pilestatus:
        filtered_df = filtered_df[filtered_df['PileStatus'] == selected_pilestatus]
    if selected_piletype:
        filtered_df = filtered_df[filtered_df['PileType'] == selected_piletype]
    if selected_productcode:
        filtered_df = filtered_df[filtered_df['ProductCode'] == selected_productcode]

    markers = []
    if len(filtered_df)>0:

        center = [np.nanmean(list(filter_none(filtered_df["latitude"]))), np.nanmean(list(filter_none(filtered_df["longitude"])))]  # Default center

        for _, row in filtered_df.iterrows():
            if pd.notna(row["latitude"]) and pd.notna(row["longitude"]):
                markers.append(dl.CircleMarker(
                                    center=[row["latitude"], row["longitude"]],
                                    radius=8,  # Bigger marker
                                    color="yellow",
                                    fill=True,
                                    fillColor="yellow",
                                    fillOpacity=0.7,
                                    # children=dl.Popup(feature.get("properties", {}).get("JobName", "Unknown"))
                                  children = dl.Popup(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")
                                ))
                if selected_pileid:  # Recenter on selected PileID
                    center = [row["latitude"], row["longitude"]]

    return markers, center,zoom_level

# Callback to track edited values and highlight changes
@app.callback(
    Output("filtered-table", "style_data_conditional"),
    [Input("filtered-table", "data_previous"), Input("group-filter", "value")],
    State("filtered-table", "data")
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
    [Input("pileid-filter", "value"), Input("date-filter", "value")]
)
def update_combined_graph(selected_pileid, selected_date):
    if not selected_pileid or selected_pileid not in pile_data or selected_date not in pile_data[selected_pileid]:
        return go.Figure(
            layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"})  # Dark background even if empty

    pile_info = pile_data[selected_pileid][selected_date]

    # Create figure with two y-axes
    fig = px.line(title=f"Depth & Strokes vs Time for PileID {selected_pileid} on {selected_date}")

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
    [Output("pileid-filter", "value"), Output("pileid-filter-top", "value")],
    [Input("pileid-filter", "value"), Input("pileid-filter-top", "value")]
)
def sync_pileid_filters(sidebar_value, top_value):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    # Determine which dropdown was changed
    changed_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if changed_id == "pileid-filter":
        return sidebar_value, sidebar_value
    else:
        return top_value, top_value

@app.callback(
    Output("save-message", "children"),
    Input("save-button", "n_clicks"),
    State("filtered-table", "data"),
    State("group-filter", "value")
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
    Input("group-filter", "value")
)
def update_columns(selected_group):
    if selected_group == "Edit":
        return [
            {"name": "Field", "id": "Field", "editable": False},
            {"name": "Value", "id": "Value", "editable": False},
            {"name": "Edited Value", "id": "Edited Value", "editable": True, "presentation": "input"}
        ]
    else:
        return [
            {"name": "Field", "id": "Field", "editable": False},
            {"name": "Value", "id": "Value", "editable": False}  # No "Edited Value" column
        ]


# Run the app
if __name__ == "__main__":
    # app.run_server(debug=True)
    app.run_server(debug=False)

#
