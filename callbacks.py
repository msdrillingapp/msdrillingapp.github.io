import dash
import pandas as pd
import dash_leaflet as dl

from dash import Output, Input, ctx, dash_table,callback_context,MATCH, State,ClientsideFunction
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from main import app, properties_df,merged_df,pile_data

from utility_funtions import filter_none


file_path = os.path.join(os.getcwd(), "assets",)
changed_values ={}
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
    if not selected_date is None:
        filtered_df = filtered_df[filtered_df["date"] == selected_date]
    if not selected_rigid is None:
        filtered_df = filtered_df[filtered_df['RigID']==selected_rigid]
    if not selected_jobid is None:
        filtered_df = filtered_df[filtered_df['JobID'] == selected_jobid]
    if not selected_pilecode is None:
        filtered_df = filtered_df[filtered_df['PileCode'] == selected_pilecode]
    if not selected_pilestatus is None:
        filtered_df = filtered_df[filtered_df['PileStatus'] == selected_pilestatus]
    if not selected_piletype is None:
        filtered_df = filtered_df[filtered_df['PileType'] == selected_piletype]
    if not selected_productcode is None:
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
    if not selected_date is None:
        filtered_df = properties_df[properties_df["date"] == selected_date]
    if not selected_jobid is None:
        filtered_df = filtered_df[filtered_df['JobID'] == selected_jobid]
    if not selected_pilecode is None:
        filtered_df = filtered_df[filtered_df['PileCode'] == selected_pilecode]
    if not selected_pilestatus is None:
        filtered_df = filtered_df[filtered_df['PileStatus'] == selected_pilestatus]
    if not selected_piletype is None:
        filtered_df = filtered_df[filtered_df['PileType'] == selected_piletype]
    if not selected_productcode is None:
        filtered_df= filtered_df[filtered_df['ProductCode'] == selected_productcode]

    return [{"label": str(p), "value": str(p)} for p in filtered_df["RigID"].dropna().unique()]

# Callback to update date based on JobID
@app.callback(
    Output("date-filter", "options"),
    [Input("jobid-filter", "value"),
     Input('pilecode-filter', "value"),
     Input('pilestatus-filter', "value"),
     Input('piletype-filter', "value"),
     Input('productcode-filter', "value"),
    Input('pileid-filter', "value")

     ], allow_duplicate=True
)
def update_date_options(selected_jobid,selected_pilecode,selected_pilestatus,selected_piletype,selected_productcode,selected_pileid):

    filtered_df = properties_df.copy()

    if not selected_jobid is None:
        filtered_df = filtered_df[filtered_df['JobID'] == selected_jobid]
    if not selected_pilecode is None:
        filtered_df = filtered_df[filtered_df['PileCode'] == selected_pilecode]
    if not selected_pilestatus is None:
        filtered_df = filtered_df[filtered_df['PileStatus'] == selected_pilestatus]
    if not selected_piletype is None:
        filtered_df = filtered_df[filtered_df['PileType'] == selected_piletype]
    if not selected_productcode is None:
        filtered_df= filtered_df[filtered_df['ProductCode'] == selected_productcode]
    if not selected_pileid is None:
        filtered_df = filtered_df[filtered_df['PileID'] == selected_productcode]


    out = list(filtered_df["date"].dropna().unique())
    out = [pd.to_datetime(x).date() for x in out]
    out.sort()
    out = [x.strftime(format='%Y-%m-%d') for x in out]
    return [{"label": str(p), "value": str(p)} for p in out]


# Callback to update map markers and recenter the map
@app.callback(
    [dash.dependencies.Output("map-markers", "children"), Output("map", "center"),Output('map','zoom')],
    [dash.dependencies.Input("date-filter", "value"),
     dash.dependencies.Input("rigid-filter", "value"),
     dash.dependencies.Input("pileid-filter", "value"),
     dash.dependencies.Input('jobid-filter', "value"),
     dash.dependencies.Input('pilecode-filter', "value"),
     dash.dependencies.Input('pilestatus-filter', "value"),
     dash.dependencies.Input('piletype-filter', "value"),
     dash.dependencies.Input('productcode-filter', "value")
     ]
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
    if not selected_pileid  is None:
        filtered_df = filtered_df[filtered_df["PileID"] == selected_pileid]
        zoom_level = 35
    if not selected_jobid is None:
        filtered_df = filtered_df[filtered_df['JobID'] == selected_jobid]
        zoom_level = 8
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
                if pile_code == "PP":  # Circle
                    marker = dl.CircleMarker(
                        center=(row["latitude"], row["longitude"]),
                        radius=5, color="blue", fill=True,
                        children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")]
                    )

                elif pile_code == "TP":  # Square (Using a rectangle as an approximation)
                    marker = dl.Rectangle(
                        bounds=[(row["latitude"] - 0.0001, row["longitude"] - 0.0001),
                                (row["latitude"] + 0.0001, row["longitude"] + 0.0001)],
                        color="green", fill=True,
                        children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")]
                    )

                elif pile_code == "RP":  # Octagon (Using a custom SVG marker)
                    marker = dl.Marker(
                        position=(row["latitude"], row["longitude"]),
                        icon={
                            "iconUrl": "https://upload.wikimedia.org/wikipedia/commons/4/4f/Octagon_icon.svg",
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
                # markers.append(dl.CircleMarker(
                #                     center=[row["latitude"], row["longitude"]],
                #                     radius=8,  # Bigger marker
                #                     color="yellow",
                #                     fill=True,
                #                     fillColor="yellow",
                #                     fillOpacity=0.7,
                #                     # children=dl.Popup(feature.get("properties", {}).get("JobName", "Unknown"))
                #                   children = dl.Popup(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")
                #                 ))
                if not selected_pileid is None:  # Recenter on selected PileID
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
# =======================================================================================
@app.callback(
    [
        # Output("date-filter", "value"),
        Output("rigid-filter", "value"),
        # Output("pileid-filter", "value"),
        # Output("pileid-filter-top", "value"),
        Output("jobid-filter", "value"),
        # Output("pilecode-filter", "value"),
        # Output("group-filter", "value")
    ],
    Input("reset-button", "n_clicks"),prevent_initial_call=True
)
# Input("date-filter", "value"),
#      Input("rigid-filter", "value"),
#      Input("pileid-filter", "value"),
#      Input('jobid-filter', "value"),
#      Input('pilecode-filter', "value"),
#      Input('pilestatus-filter', "value"),
#      Input('piletype-filter', "value"),
#      Input('productcode-filter', "value")
def reset_filters(n_clicks):
    if n_clicks > 0:
        return None, None        # Reset all filters to default (empty)
    return dash.no_update  # Don't change anything if the button hasn't been clicked




print('CALLBACK REGISTERED!')