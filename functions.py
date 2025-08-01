import numpy as np
import pandas as pd
import dash_leaflet as dl
# import dash_extensions.javascript as dj
import json
import os
import logging
# from flask_caching import Cache
# from dash import Dash
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import timedelta,datetime
import base64
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                Table, TableStyle, Frame, PageTemplate,Image)
import plotly.graph_objects as go
import math


# from celery_config import celery_app
from celery.utils.log import get_task_logger
import re
from celery import shared_task
logger = get_task_logger(__name__)

assets_path = os.path.join(os.getcwd(), "assets")
geojson_folder = os.path.join(assets_path, 'data')

columns_cpt = ['Depth (feet)','Elevation (feet)','q_c (tsf)','q_t (tsf)','f_s (tsf)','U_2 (ft-head)','U_0 (ft-head)','R_f (%)','Zone_Icn','SBT_Icn','B_q','F_r','Q_t','Ic','Q_tn','Q_s (Tons)','Q_b (Tons)','Q_ult (Tons)']
name_cpt_file_header = 'CPT-online-header.csv'
# Keep only relevant columns
filtered_columns = ["PileID", "Group", "Field", "Value", "latitude", "longitude", "date"]

# # Create a dictionary to map Field to Group
groups_df = pd.read_csv(os.path.join(assets_path,'Groups.csv'))
groups_df = groups_df.explode("Group").reset_index(drop=True)

def filter_none(lst):
    return filter(lambda x: not x is None, lst)


def extract_trailing_numbers(s):
    match = re.search(r'(\d+)$', s)
    mnum = match.group(1) if match else None
    if not mnum is None:
        try:
            mnum = int(mnum)
        except:
            mnum = None
    return mnum

# Function to load all GeoJSON files dynamically
# Cache expensive operations
# @cache.memoize(timeout=3600)
def load_geojson_data(jobID:str='1640',reload:bool=False):
    get_data = False
    if not reload:
        cache_file = _get_filepath(jobID)
        if os.path.exists(cache_file):
            (properties_df, latitudes, longitudes, markers, jobid_pile_data,groups_list,merged_df,cpt_header, jobid_cpt_data) = pd.read_pickle(cache_file)
            result_MWD = (properties_df, latitudes, longitudes, markers, jobid_pile_data,groups_list,merged_df)
            results_CPT = (cpt_header, jobid_cpt_data)
            return result_MWD,results_CPT
        else:
            get_data =True
    else:
        get_data = True

    if get_data:
        pileid_list_wrong=[]
        all_data = []
        jobid_pile_data ={}
        jobid_cpt_data = {}
        markers = []
        latitudes = []
        longitudes = []
        cpt_files_folder = 'CPT-files'
        cpt_header = {}
        for folder_name in os.listdir(geojson_folder):
            if folder_name != jobID:
                continue
            data_folder = os.path.join(geojson_folder,folder_name)
            # =========================================================
            # Process CPT data
            cpt_data ={}
            dir_cpt_data = os.path.join(data_folder, cpt_files_folder)
            if os.path.exists(dir_cpt_data):
                if os.path.isfile(os.path.join(dir_cpt_data, name_cpt_file_header)):
                    headers = pd.read_csv(os.path.join(dir_cpt_data, name_cpt_file_header))
                    # 994-402_1_cpt.mat
                    headers['Name'] = headers['File Name'].str.split('_cpt.mat').str[0]
                    cpt_header[folder_name] = headers
                    for cpt_file in os.listdir(dir_cpt_data):
                        if cpt_file == name_cpt_file_header:
                            continue
                        cpt_data_file = pd.read_csv(os.path.join(dir_cpt_data,cpt_file))
                        holeid = cpt_data_file['HoleID'].values[0] # CPT-1
                        # name_hole = headers[headers['HoleID']==holeid]['HoleID'].values[0]
                        # cpt_data_file['Name'] = name_hole
                        for c in columns_cpt:
                            if holeid in cpt_data:
                                cpt_data[holeid].update({c: list(cpt_data_file[c].values)})
                            else:
                                cpt_data[holeid] = {c: list(cpt_data_file[c].values)}
                    jobid_cpt_data[folder_name] = cpt_data
            # ===================================================

            pile_data = {}
            for filename in os.listdir(data_folder):
                if filename.endswith(".json"):
                    # file_date = filename.replace("header", "").replace(".json", "").strip()  # Extract date from filename
                    file_path = os.path.join(data_folder, filename)

                    with open(file_path, "r", encoding="utf-8") as f:
                        geojson_data = json.load(f)

                    features = geojson_data.get("features", [])

                    for feature in features:
                        properties = feature.get("properties", {})
                        geometry = feature.get("geometry", {})
                        coords = geometry.get("coordinates", [])
                        # PileCode": "PP",  "PileCode": "PRODUCTION PILE",
                        # "PileCode": "TP",  "PileCode": "TEST PILE",
                        # "PileCode": "RP", "PileCode": "REACTION PILE",
                        # "PileCode": "PB", "PileCode": "PROBE",
                        if coords and len(coords) >= 2:
                            lon, lat = coords[:2]  # Ensure correct coordinate order
                            properties["latitude"] = lat
                            properties["longitude"] = lon
                            latitudes.append(lat)
                            longitudes.append(lon)
                            try:
                                times = properties["Data"].get("Time", [])
                                time_interval = pd.to_datetime(times).to_pydatetime()
                                date2use = pd.to_datetime(time_interval[0]).date().strftime(format='%Y-%m-%d')
                            except:
                                date2use = datetime.today().date().strftime(format='%Y-%m-%d')
                                pass

                            try:
                                date = pd.to_datetime(properties['Time']).date().strftime(format='%Y-%m-%d')
                            except:
                                date = date2use
                                properties['Time'] = date

                            properties["date"] = date # Store the date from the filename

                            # PileCode - PP = circle , TestPile = square , Reaction = Octagon
                            pile_code = properties['PileCode']
                            # print(pile_code)
                            pile_status = properties['PileStatus']
                            pile_id = properties['PileID']
                            if properties['PileType'] is None:
                                properties['PileType'] = 0
                            else:
                                pileType = properties['PileType']
                            # # if not lat is None and not lon is None:
                            # #     # Assign different marker styles
                            # #     if pile_code.lower() == "PRODUCTION PILE".lower():  # Circle
                            # #
                            # #         if pileType==1:
                            # #             donut = "/assets/icons/blue-donut.png"
                            # #         else:
                            # #             donut = "/assets/icons/yellow-donut.png"
                            # #         marker = dl.Marker(
                            # #             position=(lat, lon),
                            # #             icon=dict(
                            # #                 iconUrl=donut,  # Path to your image in assets folder
                            # #                 iconSize=[30, 30]  # Size of the icon in pixels
                            # #             ),
                            # #             children=[
                            # #                 dl.Tooltip(f"PileID: {pile_id}, Status: {pile_status}")]
                            # #         )
                            # #
                            # #     elif pile_code.lower() == "TEST PILE".lower():  # Square (Using a rectangle as an approximation)
                            # #         marker = dl.Marker(
                            # #             position=(lat, lon),
                            # #             icon=dict(
                            # #                 iconUrl='assets/icons/yellow-square.png',  # Path to your image in assets folder
                            # #                 iconSize=[30, 30]  # Size of the icon in pixels
                            # #             ),
                            # #             children=[
                            # #                 dl.Tooltip(f"PileID: {pile_id}, Status: {pile_status}")]
                            # #         )
                            # #
                            # #     elif pile_code.lower() == "REACTION PILE".lower():  # Octagon (Using a custom SVG marker)
                            # #
                            # #         marker = dl.Marker(
                            # #             position=(lat, lon),
                            # #             icon=dict(
                            # #                 iconUrl='assets/icons/blue-target.png',  # Path to your image in assets folder
                            # #                 iconSize=[30, 30]  # Size of the icon in pixels
                            # #             ),
                            # #             children=[
                            # #                 dl.Tooltip(f"PileID: {pile_id}, Status: {pile_status}")]
                            # #         )
                            # #
                            # #     else:  # Default marker for other PileCodes PB "PROBE"
                            # #         marker = dl.Marker(
                            # #             position=(lat, lon),
                            # #             icon=dict(
                            # #                 iconUrl="/assets/icons/red-triangle.png",  # Path to your image in assets folder
                            # #                 iconSize=[30, 30]  # Size of the icon in pixels
                            # #             ),
                            # #             children=[
                            # #                 dl.Tooltip(f"PileID: {pile_id}, Status: {pile_status}")]
                            # #         )
                            # #
                            # #     markers.append(marker)
                            #
                            # else:
                            #     continue


                            job_id = properties.get("JobNumber")
                            if str(job_id)!=folder_name:
                                print('Error '+str(job_id))
                                pileid_list_wrong.append(pile_id)
                                properties['JobNumber'] = folder_name

                            calibration = float(properties.get("PumpCalibration"))
                            strokes = properties["Data"].get("Strokes", [])
                            volume = [calibration*float(x) for x in strokes]
                            if pile_id and "Data" in properties:
                                pile_data[pile_id] = {properties['date']: {
                                    "Time": properties["Data"].get("Time", []),
                                    "Strokes": properties["Data"].get("Strokes", []),
                                    "Depth": properties["Data"].get("Depth", []),
                                    'RotaryHeadPressure': properties['Data'].get('RotaryHeadPressure', []),
                                    'Rotation': properties['Data'].get('Rotation', []),
                                    'PenetrationRate': properties['Data'].get('PenetrationRate', []),
                                    'Pulldown': properties['Data'].get('Pulldown', []),
                                    'Torque': properties['Data'].get('Torque', []),
                                    'Volume': volume }}


                            all_data.append(properties)
            jobid_pile_data[str(job_id)] = pile_data
        # Cache the result for next time
        properties_df = pd.DataFrame(all_data)
        if 'FileName' in properties_df.columns:
            properties_df.drop(columns=['Data', 'UID', 'FileName'], inplace=True)
        else:
            properties_df.drop(columns=['Data', 'UID'], inplace=True)
        properties_df['Time'].fillna(datetime.today())
        properties_df['JobNumber'] = properties_df['JobNumber'].astype(str)
        # Melt the dataframe so each property is mapped to a Field and PileID
        melted_df = properties_df.melt(id_vars=["PileID", "latitude", "longitude", "date"], var_name="Field",
                                       value_name="Value")
        # Convert non-string values to strings to avoid DataTable errors
        melted_df["Value"] = melted_df["Value"].astype(str)
        # Merge with Groups.csv
        merged_df = melted_df.merge(groups_df, on="Field", how="left")
        merged_df["Group"].fillna("Undefined", inplace=True)  # Ensure Group is always a string

        merged_df = merged_df[filtered_columns]
        groups_list = list(merged_df["Group"].dropna().unique())
        groups_list.remove('Edit')

        result_MWD = (properties_df,  latitudes, longitudes, markers,jobid_pile_data,groups_list,merged_df)
        results_CPT = (cpt_header,jobid_cpt_data)
        result = (properties_df,  latitudes, longitudes, markers,jobid_pile_data,groups_list,merged_df,cpt_header,jobid_cpt_data)

        save_pickle(jobID,result)

    return result_MWD,results_CPT



def get_plotting_zoom_level_and_center_coordinates_from_lonlat_tuples(longitudes=None, latitudes=None):
    if ((latitudes is None or longitudes is None)
            or (len(latitudes) != len(longitudes))):
        return 0, (0, 0)

    height = max(latitudes) - min(latitudes)
    width = max(longitudes) - min(longitudes)
    center = (np.mean(longitudes), np.mean(latitudes))

    # Compute area in degrees²
    area = height * width

    # Update interpolation to realistic bounding box areas
    zoom = np.interp(
        x=area,
        xp=[0, 1**-5,0.0001, 0.001, 0.01, 0.1, 1, 10, 100],
        fp=[18, 16, 15, 13, 10, 9,8, 6, 3]
    )

    return zoom, center

def indrease_decrease_split(x,y):
    increasing_x = []
    increasing_y = []
    decreasing_x = []
    decreasing_y = []
    for i in range(1, len(y)):
        if y[i] > y[i - 1]:
            increasing_x.append(x[i])
            increasing_y.append(y[i])
        else:
            decreasing_x.append(x[i])
            decreasing_y.append(y[i])

    return increasing_x,increasing_y,decreasing_x,decreasing_y


def create_time_chart(pile_info):

    # Create figure with two y-axes
    # fig = px.line(title=f"JobID {selected_jobid} - PileID {selected_pileid} on {selected_date}")
    fig = px.line(title='')
    time_interval = pd.to_datetime(pile_info["Time"]).to_pydatetime()
    minT = min(time_interval) - timedelta(minutes=2)
    maxT = max(time_interval) + timedelta(minutes=2)
    minT = minT.strftime(format='%Y-%m-%d %H:%M:%S')
    maxT = maxT.strftime(format='%Y-%m-%d %H:%M:%S')

    # Add Depth vs Time (Secondary Y-Axis)
    depths = [-x for x in pile_info["Depth"]]
    # depths = pile_info["Strokes"]
    depth_min = min(depths)
    depth_max = max(depths)

    strokes_min = min(pile_info["Strokes"])
    strokes_max = max(pile_info["Strokes"])

    # Adjust both to include 0 and match relative proportions
    depth_range = [depth_min, depth_max]
    strokes_range = [depth_min, strokes_max] if depth_min < 0 else [strokes_min, strokes_max]

    fig.add_scatter(
        # x=pile_info["Time"],
        x=time_interval,
        y=depths,
        mode="lines",
        name="Depth",
        yaxis="y1",
        line_color="#f7b500"
    )
    # Format x-axis to show only time (HH:MM:SS)
    fig.update_xaxes(
        tickformat="%H:%M:%S",  # Format: Hours:Minutes:Seconds
    )
    # Add Strokes vs Time (Primary Y-Axis)
    fig.add_scatter(
        x=time_interval,
        y=pile_info["Strokes"],
        mode="lines+markers",  # Markers help reveal even one point
        name="Strokes",
        yaxis="y2",
        line=dict(color="green", width=3),
        marker=dict(size=6, color='lime')

    )

    # Update layout for dual y-axes and dark background
    fig.update_layout(
        yaxis=dict(title="Depth", zerolinecolor='black',side="left", showgrid=True, linecolor='black',gridcolor='rgba(100,100,100,0.5)',mirror=True,minor=dict(showgrid=True,gridcolor='rgba(100,100,100,0.5)',griddash='dot'),range=depth_range), #
        yaxis2=dict(title="Strokes",zerolinecolor='black', overlaying="y", side="right", showgrid=False, linecolor='black',position=1,range=strokes_range), #
        xaxis=dict(title="Time",zerolinecolor='black',showgrid=True, linecolor='black',gridcolor='rgba(100,100,100,0.5)',minor=dict(showgrid=True,gridcolor='rgba(100,100,100,0.5)',griddash='dot')),
        plot_bgcolor="#193153",
        paper_bgcolor="#193153",
        font=dict(color="white"),
        xaxis_range=[minT, maxT],
        # yaxis_range = [min(pile_info['Depth'])-5,max(pile_info['Depth'])+5],
        # yaxis2_range=[min(pile_info['Strokes']) - 5, max(pile_info['Strokes']) + 5],
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,  # position below the plot
            xanchor="center",
            x=0.5,
            # bgcolor="rgba(0,0,0,0.5)",  # semi-transparent background
            font=dict(size=12),  # adjust font size
            itemwidth=30,  # control item width
        )

    )

    fig.update_layout(autosize=False, height=400)
    # for trace in fig.data:
    #     print(trace.name, trace.yaxis)
    #
    # print(len(pile_info["Time"]), len(pile_info["Strokes"]))

    return fig


def create_depth_chart(pile_info,diameter=None):

    # Create figure with two y-axes
    # fig1 = px.line(title=f"JobID {selected_jobid} - PileID {selected_pileid} on {selected_date}")
    minD = min(pile_info['Depth']) - 5
    maxD = max(pile_info['Depth']) + 5
    # ================================================================================
    # Create subplots with shared y-axis
    fig1 = make_subplots(rows=1, cols=5, shared_yaxes=True, subplot_titles=("Penetration<br>Rate",
        "Rotary<br>Pressure", "Pulldown", "Rotation","Volume"))

    # Add traces
    increasing_PR, increasing_D, decreasing_PR, decreasing_D = indrease_decrease_split(pile_info["PenetrationRate"],pile_info["Depth"])
    # increasing_PR = [-x for x in increasing_PR]
    decreasing_PR = [-x for x in decreasing_PR]
    fig1.add_trace(go.Scatter(x=increasing_PR, y=increasing_D, mode='lines', line=dict(color='red', width=2), name='UP'), row=1,col=1)
    fig1.add_trace(go.Scatter(x=decreasing_PR, y=decreasing_D, mode='lines', line=dict(color='blue', width=2), name='DOWN'), row=1, col=1)
    # fig1.add_trace(go.Scatter(x=pile_info["PenetrationRate"], y=pile_info["Depth"], mode='lines', name='PenetrationRate'), row=1, col=1)
    increasing_RP, increasing_D, decreasing_RP, decreasing_D = indrease_decrease_split(pile_info["RotaryHeadPressure"],pile_info["Depth"])
    fig1.add_trace(go.Scatter(x=increasing_RP, y=increasing_D, mode='lines', line=dict(color='red', width=2), showlegend=False), row=1, col=2)
    fig1.add_trace(go.Scatter(x=decreasing_RP, y=decreasing_D, mode='lines', line=dict(color='blue', width=2), showlegend=False),row=1, col=2)
    # fig1.add_trace(go.Scatter(x=pile_info['RotaryHeadPressure'], y=pile_info["Depth"], mode='lines', name='RotaryHeadPressure'), row=1, col=2)
    increasing_Pull, increasing_D, decreasing_Pull, decreasing_D = indrease_decrease_split(pile_info["Pulldown"], pile_info["Depth"])
    fig1.add_trace(go.Scatter(x=increasing_Pull, y=increasing_D, mode='lines', line=dict(color='red', width=2), showlegend=False),row=1, col=3)
    fig1.add_trace(go.Scatter(x=decreasing_Pull, y=decreasing_D, mode='lines', line=dict(color='blue', width=2), showlegend=False),row=1, col=3)
    # fig1.add_trace(go.Scatter(x=pile_info['Pulldown'], y=pile_info["Depth"], mode='lines', name='Pulldown'), row=1, col=3)
    increasing_Rot, increasing_D, decreasing_Rot, decreasing_D = indrease_decrease_split(pile_info["Rotation"],pile_info["Depth"])
    fig1.add_trace(go.Scatter(x=increasing_Rot, y=increasing_D, mode='lines', line=dict(color='red', width=2), showlegend=False), row=1, col=4)
    fig1.add_trace(go.Scatter(x=decreasing_Rot, y=decreasing_D, mode='lines', line=dict(color='blue', width=2), showlegend=False),row=1, col=4)
    # fig1.add_trace(go.Scatter(x=pile_info['Rotation'], y=pile_info["Depth"], mode='lines', name='Rotation'), row=1, col=4)
    fig1.add_trace(go.Scatter(x=pile_info["Volume"], y=pile_info["Depth"], name='Actual' , mode='lines', line=dict(color='black', width=2), showlegend=True),row=1, col=5)
    if not diameter is None:
        minDepth = float(min(pile_info["Depth"]))
        volume_cy = cylinder_volume_cy(diameter,-minDepth)
        fig1.add_trace(go.Scatter(x=[volume_cy,0],y=[0,minDepth],mode='lines',name = 'Theoretical',line=dict(color='grey', width=2, dash='dashdot'), showlegend=True),row=1,col=5)
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
            y=-0.3,  # position below the plot
            xanchor="center",
            x=0.5,
            # bgcolor="rgba(0,0,0,0.5)",  # semi-transparent background
            font=dict(size=11),  # adjust font size
            itemwidth=30,  # control item width
        )
    )
    fig1.update_annotations(font_size=11)
    fig1.update_yaxes(range=[minD, maxD])
    tils = ['(ft/min)', '(bar)', '(tons)', '(rpm)','(yd^3)']
    for i in range(0, 5):
        fig1.update_xaxes(title_text=tils[i], row=1, col=i + 1)

    # Configure gridlines for each subplot
    for i in range(0, 5):
        fig1.update_xaxes(
            zerolinecolor = 'black',
            gridcolor='rgba(100,100,100,0.5)',
            gridwidth=1,
            showgrid=True,
            linecolor='black',
            mirror=True,
            minor=dict(showgrid=True, gridcolor='rgba(100,100,100,0.5)', griddash='dot'),
            row=1,
            col=i+1
        )
        fig1.update_yaxes(
            zerolinecolor='black',
            gridcolor='rgba(100,100,100,0.5)',
            gridwidth=1,
            showgrid=True,
            linecolor='black',
            mirror=True,
            minor=dict(showgrid=True, gridcolor='rgba(100,100,100,0.5)', griddash='dot'),
            row=1,
            col=i+1
        )

    # fig1.update_layout(
    #     autosize=True,
    #     margin=dict(l=20, r=20, b=20, t=30),
    # )
    fig1.update_layout(autosize=False, height=700)

    return fig1
# ===============================================================================
def create_depth_chart_small_screen(pile_info,diameter=None):

    # Create figure with two y-axes
    # fig1 = px.line(title=f"JobID {selected_jobid} - PileID {selected_pileid} on {selected_date}")
    minD = min(pile_info['Depth']) - 5
    maxD = max(pile_info['Depth']) + 5
    # ================================================================================
    # Create subplots with shared y-axis
    fig1 = make_subplots(rows=5, cols=1, shared_yaxes=True, subplot_titles=("Penetration<br>Rate",
        "Rotary<br>Pressure", "Pulldown", "Rotation","Volume"))

    # Add traces
    increasing_PR, increasing_D, decreasing_PR, decreasing_D = indrease_decrease_split(pile_info["PenetrationRate"],pile_info["Depth"])
    fig1.add_trace(go.Scatter(x=increasing_PR, y=increasing_D, mode='lines', line=dict(color='red', width=2), name='UP'), row=1,col=1)
    fig1.add_trace(go.Scatter(x=decreasing_PR, y=decreasing_D, mode='lines', line=dict(color='blue', width=2), name='DOWN'), row=1, col=1)
    # fig1.add_trace(go.Scatter(x=pile_info["PenetrationRate"], y=pile_info["Depth"], mode='lines', name='PenetrationRate'), row=1, col=1)
    increasing_RP, increasing_D, decreasing_RP, decreasing_D = indrease_decrease_split(pile_info["RotaryHeadPressure"],pile_info["Depth"])
    fig1.add_trace(go.Scatter(x=increasing_RP, y=increasing_D, mode='lines', line=dict(color='red', width=2), showlegend=False), row=2, col=1)
    fig1.add_trace(go.Scatter(x=decreasing_RP, y=decreasing_D, mode='lines', line=dict(color='blue', width=2), showlegend=False),row=2, col=1)
    # fig1.add_trace(go.Scatter(x=pile_info['RotaryHeadPressure'], y=pile_info["Depth"], mode='lines', name='RotaryHeadPressure'), row=1, col=2)
    increasing_Pull, increasing_D, decreasing_Pull, decreasing_D = indrease_decrease_split(pile_info["Pulldown"], pile_info["Depth"])
    fig1.add_trace(go.Scatter(x=increasing_Pull, y=increasing_D, mode='lines', line=dict(color='red', width=2), showlegend=False),row=3, col=1)
    fig1.add_trace(go.Scatter(x=decreasing_Pull, y=decreasing_D, mode='lines', line=dict(color='blue', width=2), showlegend=False),row=3, col=1)
    # fig1.add_trace(go.Scatter(x=pile_info['Pulldown'], y=pile_info["Depth"], mode='lines', name='Pulldown'), row=1, col=3)
    increasing_Rot, increasing_D, decreasing_Rot, decreasing_D = indrease_decrease_split(pile_info["Rotation"],pile_info["Depth"])
    fig1.add_trace(go.Scatter(x=increasing_Rot, y=increasing_D, mode='lines', line=dict(color='red', width=2), showlegend=False), row=4, col=1)
    fig1.add_trace(go.Scatter(x=decreasing_Rot, y=decreasing_D, mode='lines', line=dict(color='blue', width=2), showlegend=False),row=4, col=1)
    # fig1.add_trace(go.Scatter(x=pile_info['Rotation'], y=pile_info["Depth"], mode='lines', name='Rotation'), row=1, col=4)
    fig1.add_trace(go.Scatter(x=pile_info["Volume"], y=pile_info["Depth"], name='Actual' , mode='lines', line=dict(color='black', width=2), showlegend=True),row=5, col=1)
    if not diameter is None:
        minDepth = float(min(pile_info["Depth"]))
        volume_cy = cylinder_volume_cy(diameter,-minDepth)
        fig1.add_trace(go.Scatter(x=[volume_cy,0],y=[0,minDepth],mode='lines',name = 'Theoretical',line=dict(color='grey', width=2, dash='dashdot'), showlegend=True),row=5,col=1)
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
            y=-0.3,  # position below the plot
            xanchor="center",
            x=0.5,
            # bgcolor="rgba(0,0,0,0.5)",  # semi-transparent background
            font=dict(size=11),  # adjust font size
            itemwidth=30,  # control item width
        ),
        height = 1000,
        # vertical_spacing=0.05
    )
    fig1.update_annotations(font_size=11)
    fig1.update_yaxes(range=[minD, maxD])
    tils = ['(ft/min)', '(bar)', '(tons)', '(rpm)','(yd^3)']
    for i in range(0, 5):
        fig1.update_xaxes(title_text=tils[i], row=i+1, col=1)

    # Configure gridlines for each subplot
    for i in range(0, 5):
        fig1.update_xaxes(
            zerolinecolor = 'black',
            gridcolor='rgba(100,100,100,0.5)',
            gridwidth=1,
            showgrid=True,
            linecolor='black',
            mirror=True,
            minor=dict(showgrid=True, gridcolor='rgba(100,100,100,0.5)', griddash='dot'),
            row=i+1,
            col=1
        )
        fig1.update_yaxes(
            zerolinecolor='black',
            gridcolor='rgba(100,100,100,0.5)',
            gridwidth=1,
            showgrid=True,
            linecolor='black',
            mirror=True,
            minor=dict(showgrid=True, gridcolor='rgba(100,100,100,0.5)', griddash='dot'),
            row=i+1,
            col=1
        )

    # fig1.update_layout(
    #     autosize=True,
    #     # margin=dict(l=20, r=20, b=20, t=30),
    # )

    return fig1
# ===============================================================================



def cylinder_volume_cy(diameter_inches, height_feet):
    """
    Calculate the volume of a cylinder in cubic yards.

    Parameters:
    diameter_inches (float): Diameter of the cylinder in inches
    height_feet (float): Height of the cylinder in feet

    Returns:
    float: Volume in cubic yards
    """
    # Convert diameter from inches to yards (36 inches = 1 yard)
    diameter_yards = diameter_inches / 36
    radius_yards = diameter_yards / 2

    # Convert height from feet to yards (3 feet = 1 yard)
    height_yards = height_feet / 3

    # Calculate volume in cubic yards: V = πr²h
    volume = math.pi * (radius_yards ** 2) * height_yards

    return volume

# def adjust_for_single_page(story, max_height=10.5*inch):
#     total_height = sum([item.wrap(0,0)[1] if hasattr(item, 'wrap') else item for item in story])
#     if total_height > max_height:
#         scale_factor = max_height / total_height * 0.95  # 5% margin
#         for item in story:
#             if isinstance(item, Image):
#                 item.drawWidth *= scale_factor
#                 item.drawHeight *= scale_factor

# 1. Define a function to get absolute paths safely
def get_app_root():
    """Safely get the application root path in any context"""
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except:
        return os.getcwd()
# @celery_app.task(bind=True)
# Add this to your imports
# from pathlib import Path



def create_jobid_timechart(pile_data4jobid, selected_date=None):
    tmp_time = []
    tmp_stk = []
    tmp_depth = []
    for v1 in pile_data4jobid.values():
        for v2 in v1.values():
            tmp_time.extend(v2['Time']) # this is a list
            tmp_stk.extend(v2['Strokes'])
            tmp_depth.extend(v2['Depth'])

    # dictionary of lists
    dict = {'Time': tmp_time, 'Strokes': tmp_stk, 'Depth': tmp_depth}
    df = pd.DataFrame(dict)
    df['Time'] = pd.to_datetime(df['Time'])
    df.sort_values(by=['Time'],inplace=True)
    return df

#
def generate_mwd_pdf(selected_row, time_fig, depth_fig):
    # Get absolute path to templates/assets
    # app_root = Path(get_app_root())
    # template_path = app_root / 'templates' / 'report_template.html'
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            leftMargin=0.5 * inch,
                            rightMargin=0.5 * inch,
                            topMargin=0.5 * inch,
                            bottomMargin=0.5 * inch)

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=14,
        leading=16,
        spaceAfter=12,
        alignment=1  # Center
    )

    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=12,
        leading=14,
        spaceAfter=6,
        textColor=colors.black
    )

    # Convert Plotly figures to images
    # Enhance visibility for PDF export
    for fig in [time_fig, depth_fig]:
        fig['layout']['plot_bgcolor'] = 'white'
        fig['layout']['paper_bgcolor'] = 'white'
        fig['layout']['font']['color'] = 'black'
        # Set axis title and tick font sizes
        # fig['layout']['yaxis']['titlefont'] = {'size': 14,'family': 'Helvetica, sans-serif','color': 'black'}
        # fig['layout']['yaxis']['tickfont'] = {'size': 12,'family': 'Helvetica-Bold, sans-serif','color': 'black'}
        # fig['layout']['xaxis']['titlefont'] = {'size': 14,'family': 'Helvetica, sans-serif','color': 'black'}
        # fig['layout']['xaxis']['tickfont'] = {'size': 12,'family': 'Helvetica-Bold, sans-serif','color': 'black'}


        # Make gridlines more prominent in PDF
        fig['layout']['xaxis']['gridcolor'] = 'rgba(70, 70, 70, 0.7)'  # Darker gray
        fig['layout']['xaxis']['gridwidth'] = 1.2
        fig['layout']['yaxis']['gridcolor'] = 'rgba(70, 70, 70, 0.7)'
        fig['layout']['yaxis']['gridwidth'] = 1.2

        # Increase line widths for better visibility
        if 'data' in fig and len(fig['data']) > 0:
            if 'line' in fig['data'][0]:
                fig['data'][0]['line']['width'] = 3

    time_img = BytesIO()
    go.Figure(time_fig).write_image(time_img, format='png', scale=3)  # Higher resolution
    time_img.seek(0)

    # Special handling for subplots in depth chart
    # if 'subplots' in depth_fig.get('layout', {}):
    for axis in depth_fig['layout']:
        if axis.startswith(('xaxis', 'yaxis')):
            depth_fig['layout'][axis]['gridcolor'] = 'rgba(100,100,100,0.7)'
            depth_fig['layout'][axis]['gridwidth'] = 1.2
            depth_fig['layout'][axis]['showgrid'] = True
            # depth_fig['layout'][axis]['titlefont'] = {'size': 16,'family': 'Helvetica, sans-serif','color': 'black'}
            # depth_fig['layout'][axis]['tickfont'] = {'size': 14,'family': 'Helvetica-Bold, sans-serif', 'color': 'black'}

    depth_img = BytesIO()
    # go.Figure(depth_fig).write_image(depth_img, format='png', scale=2)
    # 4x resolution
    go.Figure(depth_fig).write_image(depth_img,scale=4)
    depth_img.seek(0)


    # Create content
    story = []
    LOGO_PATH = assets_path + '/MSB.logo.JPG'

    header_table = Table(
        [
            [
                Paragraph("Morris Shea Pile Drill Log", title_style),
                Image(LOGO_PATH, width=1 * inch, height=0.75 * inch) if os.path.exists(LOGO_PATH) else Spacer(1, 1)
            ]
        ],
        colWidths=[5.5 * inch, 1.5 * inch]  # Adjust width as needed
    )

    header_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # Center title
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),  # Align logo to the right
    ]))

    story.append(header_table)

    # Job Site Data
    date_drill = pd.to_datetime(selected_row.get('Time', '')).date().strftime(format='%Y-%m-%d')
    job_data = [
        ["JOB ID:", selected_row.get('JobID', '')],
        ["CLIENT:", "Morris Shea Bridge"],#selected_row.get('Client', '')
        ["CONTRACTOR:", "Morris Shea Bridge"],
        ["DATE:", date_drill],
        ['','']
    ]

    # Pile Data
    pile_data = [
        ["PILE No:", f"{selected_row.get('PileID', '')}"],
        ["START TIME:", selected_row.get('DrillStartTime', '')],
        ["END TIME:", selected_row.get('DrillEndTime', '')],
        ["TOTAL TIME:", selected_row.get('Totaltime', '')],
        ["RIG:", selected_row.get('RigID', '')],
        # ["OPERATOR:", selected_row.get('OPERATOR', '')],

    ]
    try:
        diameter = str(round(float(selected_row.get('PileDiameter', '')),2))
    except:
        diameter = str(selected_row.get('PileDiameter', ''))
    pile_data_2 = [["PILE LENGTH:", str(selected_row.get('PileLength', ''))+' [ft]'],
        ["PILE DIAMETER:", diameter +' [in]'],
        ["STROKES:", selected_row.get('MaxStrokes', '')],
        ["PUMP CALIB.:", str(selected_row.get('Calibration', ''))+' [cy/str]'],
        ["OVER BREAK:", selected_row.get('OverBreak', '')]]

    maxdepth = str(selected_row.get('MinDepth',''))
    # Combine tables horizontally
    # Make sub-tables
    # Width for each column = total header width / 3
    col_width = 7.0 / 3 * inch  # approx 2.33 inches

    # Build job_data, pile_data, and pile_data_2 tables with matching widths
    job_table = Table(job_data, colWidths=[1.1 * inch, col_width - 1.1 * inch], style=[
        ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ])

    pile_table = Table(pile_data, colWidths=[1.1 * inch, col_width - 1.1 * inch], style=[
        ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ])

    pile_table_2 = Table(pile_data_2, colWidths=[1.1 * inch, col_width - 1.1 * inch], style=[
        ('BOX', (0, 0), (-1, -1), 0.8, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ])

    # Combine them into one row
    combined_tables = Table(
        [[job_table, pile_table, pile_table_2]],
        colWidths=[col_width] * 3
    )

    # Set consistent styling across the row
    combined_tables.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.2, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),

    ]))

    # Add some vertical spacing before this block
    story.append(Spacer(1, 0))
    story.append(combined_tables)


    # Add charts with frames
    # Combined charts in one box
    charts_table = Table([
        [Paragraph("Time Scale", header_style)],
        [Image(time_img, width=6 * inch, height=2.5 * inch)],
        [Paragraph("Depth ("+ maxdepth+" ft)", header_style)],
        [Image(depth_img, width=7. * inch, height=4. * inch)]
    ],
        colWidths=[7 * inch],  # 👈 force total width
        style=[
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5)
        ])

    story.append(charts_table)

    # Build PDF
    file_name = 'JobID_' + str(selected_row.get('JobID', '')) + '_PileID_' + str(
        selected_row.get('PileID', '')) + '_Time_' + str(selected_row.get('Time', '')) + '.pdf'
    doc.build(story)
    buffer.seek(0)
    pdf_data = base64.b64encode(buffer.read()).decode('utf-8')
    return {
        'content': pdf_data,
        'filename': file_name,
        'type': 'application/pdf',
        'base64': True
    }

# ========================================================================
DATA_DIR = 'assets//pkl'

def _get_filepath(job_number):
    return os.path.join(DATA_DIR, f"{job_number}.pkl")

def load_pickle(job_number):
    path = _get_filepath(job_number)
    if os.path.exists(path):
        return pd.read_pickle(path)

    return None

def save_pickle(job_number, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    pd.to_pickle(data, _get_filepath(job_number))


def get_last_updated(job_number):
    path = _get_filepath(job_number)
    if os.path.exists(path):
        ts = os.path.getmtime(path)
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    return "No cache available"

# ===============================================================
# @celery_app.task
# @celery.task(bind=True)
# def generate_all_pdfs_task(all_rows,pile_data):
#     zip_buffer = io.BytesIO()
#     with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
#         for row in all_rows:
#             pileid = row['PileID']
#             time = row['Time']
#             try:
#                 date = pd.to_datetime(time).date().strftime('%Y-%m-%d')
#             except Exception:
#                 continue
#             pile_info = pile_data[pileid][date]
#             time_fig = create_time_chart(pile_info)
#             depth_fig = create_depth_chart(pile_info)
#             try:
#                 pdf_dict = generate_mwd_pdf(row, time_fig, depth_fig)
#                 pdf_bytes = base64.b64decode(pdf_dict['content'])
#                 zip_file.writestr(pdf_dict['filename'], pdf_bytes)
#             except Exception as e:
#                 print(f"PDF generation failed: {str(e)}")
#                 continue
#
#     zip_buffer.seek(0)
#     zip_data = base64.b64encode(zip_buffer.read()).decode('utf-8')
#     return {
#         'content': zip_data,
#         'filename': 'all_pile_reports.zip',
#         'type': 'application/zip',
#         'base64': True
#     }
#
# @celery_app.task(name="generate_all_pdfs_task")
# def generate_all_pdfs_task(all_rows, pile_data):
#     # Get logger specifically for this task
#     logger = logging.getLogger('celery.task')
#     logger.propagate = True  # Ensure logs propagate to root
#     logger.setLevel(logging.DEBUG)
#     logger.info("🚀 Task started with %d rows", len(all_rows))
#
#     print("=== TASK STARTED ===")
#
#     zip_buffer = io.BytesIO()
#     # raise Exception("Test error to see if this hits the logs.")
#     with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
#         for row in all_rows:
#             pileid = row['PileID']
#             time = row['Time']
#             try:
#                 date = pd.to_datetime(time).date().strftime('%Y-%m-%d')
#             except Exception:
#                 continue
#             pile_info = pile_data[pileid][date]
#             time_fig = create_time_chart(pile_info)
#             depth_fig = create_depth_chart(pile_info)
#             try:
#                 pdf_dict = generate_mwd_pdf(row, time_fig, depth_fig)
#                 pdf_bytes = base64.b64decode(pdf_dict['content'])
#                 zip_file.writestr(pdf_dict['filename'], pdf_bytes)
#                 logger.info(f"Added PDF for pile {pileid} to zip.")
#             except Exception as e:
#                 print(f"PDF generation failed: {str(e)}")
#                 logger.error(f"Failed to generate PDF for pile {pileid}: {e}")
#                 continue
#
#     zip_buffer.seek(0)
#
#     # Save to file
#     root_path = get_app_root()
#     filename = "report.zip"
#     filepath = os.path.join(root_path, "instance", "tmp", filename)
#     os.makedirs(os.path.dirname(filepath), exist_ok=True)
#
#     try:
#         with open(filepath, "wb") as f:
#             f.write(zip_buffer.read())
#         logger.info(f"ZIP file saved to {filepath}")
#     except Exception as e:
#         logger.error(f"Error saving zip file: {e}")
#         return "Error filepath:" + filepath
#
#     print("Returning filename:", filename)
#
#     return filename
# ================================================================================
# ================================================================================
# ================================================================================
# ================================================================================
# ================================================================================
# ================================================================================
# # # Create a dictionary to map Field to Group
# groups_df = pd.read_csv(os.path.join(assets_path,'Groups.csv'))
# groups_df = groups_df.explode("Group").reset_index(drop=True)
# (properties_df, latitudes,longitudes,markers,jobid_pile_data,merged_df,groups_list),(cpt_header,jobid_cpt_data) = load_geojson_data()
# if 'FileName' in properties_df.columns:
#     properties_df.drop(columns=['Data','UID','FileName'],inplace=True)
# else:
#     properties_df.drop(columns=['Data', 'UID'], inplace=True)
# properties_df['Time'].fillna(datetime.today())
# properties_df['JobNumber'] = properties_df['JobNumber'].astype(str)
# # Melt the dataframe so each property is mapped to a Field and PileID
# melted_df = properties_df.melt(id_vars=["PileID","latitude", "longitude", "date"], var_name="Field", value_name="Value")
# # Convert non-string values to strings to avoid DataTable errors
# melted_df["Value"] = melted_df["Value"].astype(str)
# # Merge with Groups.csv
# merged_df = melted_df.merge(groups_df, on="Field", how="left")
# merged_df["Group"].fillna("Undefined", inplace=True)  # Ensure Group is always a string
#
# merged_df = merged_df[filtered_columns]
# groups_list = list(merged_df["Group"].dropna().unique())
# groups_list.remove('Edit')

(properties_df, latitudes,longitudes,markers,jobid_pile_data,merged_df,groups_list),(cpt_header,jobid_cpt_data) = load_geojson_data()






