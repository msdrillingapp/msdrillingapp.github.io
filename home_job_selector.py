import dash
import os
from datetime import datetime
from dash import dcc, html, Output, Input, State,no_update,callback
from functions import get_last_updated,load_geojson_data

dash.register_page(__name__,'/')

if '__file__' in globals():
    root_path = os.path.dirname(os.path.abspath(__file__))
else:
    # Fallback for environments where __file__ isn't available
    root_path = os.getcwd()

assets_path = os.path.join(os.getcwd(), "assets")
geojson_folder = os.path.join(assets_path, 'data')

job_numbers = os.listdir(geojson_folder)

layout = html.Div([

    dcc.Store(id='shared-job-data-mwd', storage_type='memory'),
    dcc.Store(id='shared-job-data-cpt', storage_type='memory'),
    dcc.Store(id='selected-jobnumber', storage_type='memory'),

    html.H2("Load Job Data"),

    dcc.Dropdown(
        id='job-number-dropdown',
        options=[{'label': jn, 'value': jn} for jn in job_numbers],
        placeholder='Select a JobNumber'
    ),

    dcc.RadioItems(
        id='load-method-radio',
        options=[
            {'label': 'Load Cached (.pkl)', 'value': 'cached'},
            {'label': 'Reload from API', 'value': 'api'}
        ],
        value='cached',
        inline=True
    ),

    html.Button("Load Data", id='load-button', n_clicks=0),

    html.Div(id='last-updated-div', style={'marginTop': '10px'}),

    html.Div(id='data-output', style={'marginTop': '20px'}),
])


@callback(Output('shared-job-data-mwd', 'data'),
Output('shared-job-data-cpt', 'data'),
Output('selected-jobnumber', 'data'),
    Output('data-output', 'children'),
    Output('last-updated-div', 'children'),
    Input('load-button', 'n_clicks'),
    State('job-number-dropdown', 'value'),
    State('load-method-radio', 'value')
)
def handle_load(n_clicks, job_number, load_method):
    if not job_number:
        return dash.no_update, dash.no_update,dash.no_update,  "Please select a JobNumber.", ""

    if load_method == 'cached':
        results_MWD, results_CPT  = load_geojson_data(job_number,False)
        last_updated = get_last_updated(job_number)
        message = f"Loaded cached data for {job_number}."
    else:
        results_MWD, results_CPT  = load_geojson_data(job_number,True)
        last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"Fetched fresh data for {job_number}."

    # Unpack CPT tuple into dict for serialization
    cpt_header, jobid_cpt_data = results_CPT
    data_cpt_dict = {
        "cpt_header": cpt_header,
        "jobid_cpt_data": jobid_cpt_data
    }

    # Same for MWD if needed
    (properties_df, latitudes, longitudes, markers,
     jobid_pile_data, groups_list, merged_df) = results_MWD

    data_mwd_dict = {
        "properties_df": properties_df.to_dict("records"),
        "latitudes": latitudes,
        "longitudes": longitudes,
        "markers": markers,
        "jobid_pile_data": jobid_pile_data,
        "groups_list": groups_list,
        "merged_df":  merged_df.to_dict("records")
    }
    import json
    print(json.dumps(data_mwd_dict))
    return data_mwd_dict, data_cpt_dict,job_number, message, f"Last updated: {last_updated}"





# =================================================================================================
# # ==================================================================================================
# # Callback to update map markers and recenter the map
# @callback(
#     [Output("map-markers", "children"),
#      Output("map", "center"),
#      Output('map','zoom'),
#      Output("map", "key")],
#     [Input("date-filter", "value"),
#      Input("rigid-filter", "value"),
#      Input("pileid-filter", "value"),
#      Input('jobid-filter', "value"),
#      Input('pilecode-filter', "value"),
#      Input('pilestatus-filter', "value"),
#      Input('piletype-filter', "value"),
#      Input('productcode-filter', "value")
#      ]#,prevent_initial_call=True
# )
# def update_map_markers(selected_date, selected_rigid, selected_pileid,selected_jobid,selected_pilecode,selected_pilestatus,selected_piletype,selected_productcode):
#     filtered_df = properties_df.copy()
#
#     center = [np.nanmean(list(filter_none(properties_df["latitude"]))), np.nanmean(list(filter_none(properties_df["longitude"])))]
#     zoom_level = 8
#     # Apply filters
#     if not selected_date is None:
#         filtered_df = filtered_df[filtered_df["date"] == selected_date]
#     if not selected_rigid is None:
#         filtered_df = filtered_df[filtered_df["RigID"] == selected_rigid]
#         zoom_level = 20
#     if not selected_pileid is None:
#         filtered_df = filtered_df[filtered_df["PileID"] == selected_pileid]
#         zoom_level = 45
#     if not selected_jobid is None:
#         filtered_df = filtered_df[filtered_df['JobNumber'] == selected_jobid]
#         zoom_level = 20
#     if not selected_pilecode is None:
#         filtered_df = filtered_df[filtered_df['PileCode'] == selected_pilecode]
#     if not selected_pilestatus is None:
#         filtered_df = filtered_df[filtered_df['PileStatus'] == selected_pilestatus]
#     if not selected_piletype is None:
#         filtered_df = filtered_df[filtered_df['PileType'] == selected_piletype]
#     if not selected_productcode is None:
#         filtered_df = filtered_df[filtered_df['ProductCode'] == selected_productcode]
#
#     markers = []
#     if len(filtered_df)>0:
#
#         center = [np.nanmean(list(filter_none(filtered_df["latitude"]))), np.nanmean(list(filter_none(filtered_df["longitude"])))]  # Default center
#
#         for _, row in filtered_df.iterrows():
#             if pd.notna(row["latitude"]) and pd.notna(row["longitude"]):
#                 pile_code = row.get("PileCode", "")
#                 piletype = row.get("PileType", "")
#
#                 # Assign different marker styles
#                 if pile_code.lower() == "Production Pile".lower():  # Circle
#                     if piletype == 1:
#                         donut = "/assets/blue-donut.png"
#                     else:
#                         donut = "/assets/yellow-donut.png"
#                     marker = dl.Marker(
#                         position=(row["latitude"], row["longitude"]),
#                         icon=dict(
#                             iconUrl=donut,  # Path to your image in assets folder
#                             iconSize=[10, 10]  # Size of the icon in pixels
#                         ),
#                         children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")]
#                     )
#
#                 elif pile_code.lower() == "TEST PILE".lower():  # Square (Using a rectangle as an approximation)
#                     marker = dl.Marker(
#                         position=(row["latitude"], row["longitude"]),
#                         icon=dict(
#                             iconUrl='assets/yellow-square.png',  # Path to your image in assets folder
#                             iconSize=[10, 10]  # Size of the icon in pixels
#                         ),
#                         children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")]
#                     )
#
#                 elif pile_code.lower() == "REACTION PILE".lower():  # Octagon (Using a custom SVG marker)
#                     marker = dl.Marker(
#                         position=(row["latitude"], row["longitude"]),
#                         icon=dict(
#                             iconUrl='assets/blue-target.png',  # Path to your image in assets folder
#                             iconSize=[10, 10]  # Size of the icon in pixels
#                         ),
#                         children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")]
#                     )
#
#                 else:  # Default marker for other PileCodes Probe
#                     marker = dl.Marker(
#                         position=(row["latitude"], row["longitude"]),
#                         icon=dict(
#                             iconUrl="/assets/red-triangle.png",  # Path to your image in assets folder
#                             iconSize=[10, 10]  # Size of the icon in pixels
#                         ),
#                         children=[dl.Tooltip(f"PileID: {row['PileID']}, Status: {row.get('PileStatus', 'Unknown')}")]
#                     )
#                 center = [row["latitude"], row["longitude"]]
#                 markers.append(marker)
#
#                 if not selected_pileid is None:  # Recenter on selected PileID
#                     center = [row["latitude"], row["longitude"]]
#
#     return markers, center,zoom_level, f"map-{center_lat}-{center_lon}-{zoom_level}"
#
#
# # Callbacks to toggle each collapsible section
# @callback(
#     Output("collapse-map", "is_open"),
#     [Input("toggle-map", "n_clicks")],
#     [State("collapse-map", "is_open")],prevent_initial_call=True
# )
# def toggle_map(n_clicks, is_open):
#     if n_clicks:
#         return not is_open
#     return is_open
