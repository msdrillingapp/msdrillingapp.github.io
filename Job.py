import json
import pandas as pd
from datetime import datetime,timedelta
from typing import List, Dict, Optional
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import holidays
import math
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,Image,PageBreak
from reportlab.lib.units import inch
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.platypus import NextPageTemplate
# from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT,TA_RIGHT

assets_path = os.path.join(os.getcwd(),'assets')

columns_cpt = ['Depth (feet)','Elevation (feet)','q_c (tsf)','q_t (tsf)','f_s (tsf)','U_2 (ft-head)','U_0 (ft-head)','R_f (%)','Zone_Icn','SBT_Icn','B_q','F_r','Q_t','Ic','Q_tn','Q_s (Tons)','Q_b (Tons)','Q_ult (Tons)']
name_cpt_file_header = 'CPT-online-header.csv'


def format_time_to_hours_minutes(time_str):
    """Convert HH:MM:SS to Xh Ym format"""
    try:
        hours, minutes, seconds = map(int, time_str.split(':'))

        # Handle cases where we might have seconds that round up minutes
        if seconds >= 30:
            minutes += 1

        # Format as Xh Ym, omitting zero values
        if hours == 0 and minutes == 0:
            return "0h"  # or return "" if you want to exclude zeros completely
        elif hours == 0:
            return f"{minutes}m"
        elif minutes == 0:
            return f"{hours}h"
        else:
            return f"{hours}h {minutes}m"
    except:
        return time_str  # return original if format is invalid

# Convert H:M:S to total seconds and sum
def sum_times_to_hours_minutes(series):
    # Convert string to timedelta
    series = pd.to_timedelta(series)

    # Sum all timedeltas
    total_time = series.sum()

    # Convert to hours and minutes
    total_hours = total_time.total_seconds() / 3600
    hours = int(total_hours)
    minutes = int((total_hours - hours) * 60)
    # Format as Xh Ym, omitting zero values
    if hours == 0 and minutes == 0:
        return "0h"
    elif hours == 0:
        return f"{minutes}m"
    elif minutes == 0:
        return f"{hours}h"
    else:
        return f"{hours}h {minutes}m"



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
def indrease_decrease_split(x, y):
    min_index = y.index(min(y))

    # Increasing segment: from start to min_index
    increasing_x = []
    increasing_y = []
    for i in range(1, min_index + 1):

        increasing_x.append(x[i])
        increasing_y.append(y[i])

    # Decreasing segment: from min_index to end
    decreasing_x = []
    decreasing_y = []
    for i in range(min_index + 1, len(y)):
        decreasing_x.append(x[i])
        decreasing_y.append(y[i])


    return increasing_x, increasing_y, decreasing_x, decreasing_y



# Create US holidays object
us_holidays = holidays.US()
# Calculate working days
def is_working_day(date):
    # Check if weekend (Saturday=5, Sunday=6)
    if date.weekday() >= 5:
        return False
    # Check if holiday
    if date in us_holidays:
        return False
    return True


def next_working_day(date):
    next_day = date + timedelta(days=1)
    while not is_working_day(next_day):
        next_day += timedelta(days=1)
    return next_day




class Pile:
    def __init__(self, data,pile_data):
        self.data = data
        self.pile_id = self.data.PileID
        self.job_id = self.data.JobNumber
        self.job_name = self.data.JobName
        self.client = self.data.Client

        self.pileType = str(self.data.PileType)
        if (self.pileType is None) or (self.pileType  == 'nan'):
            self.pileType = 'None'

        self.productCode = self.data.ProductCode
        if (self.productCode is None) or (self.productCode == ''):
            self.productCode = 'DWP'

        self.pileStatus = self.data.PileStatus
        self.pileCode = self.data.PileCode
        self.rig = self.data.RigID
        self.diameter = self.data.PileDiameter
        self.length = self.data.PileLength
        self.locationid = self.data.LocationID
        self.drillStartTime = self.data.DrillStartTime
        self.drillEndTime = self.data.DrillEndTime
        self.drillTime = self.data.DrillTime
        self.groutVolume = self.data.GroutVolume
        self.groutTime = self.data.GroutTime
        self.installTime = self.data.InstallTime
        self.moveTime = self.data.MoveTime
        self.cycleTime = self.data.CycleTime
        self.delayTime = self.data.DelayTime
        self.overbreak = self.data.OverBreak
        self.pileArea = self.data.PileArea
        self.pileVolume = self.data.PileVolume
        self.calibration = float(self.data.PumpCalibration)
        self.longitude = self.data.longitude
        self.latitude = self.data.latitude

        self.time = pile_data['Time']
        try:
            self.datetime_array = [datetime.strptime(t, "%d.%m.%Y %H:%M:%S") for t in self.time]
        except:
            self.datetime_array = [datetime.strptime(t, "%Y-%m-%d %H:%M:%S") for t in self.time]
        self.depth = pile_data['Depth']
        self.pressure = pile_data['RotaryHeadPressure']
        self.rotation = pile_data['Rotation']
        self.torque = pile_data['Torque']
        self.strokes = pile_data['Strokes']
        volume = [self.calibration * float(x) for x in self.strokes]
        self.volume = volume
        self.pulldown = pile_data['Pulldown']
        self.penetration_rate = pile_data['PenetrationRate']

        self.maxstrokes = max(self.strokes)
        self.mindepth = min(self.depth)

        # geometry = pile_data.get("geometry", {})
        # coords = geometry.get("coordinates", [])
        # lon = None
        # lat = None
        # if coords and len(coords) >= 2:
        #     lon, lat = coords[:2]
        # self.longitude = self.data['longitude']
        # self.latitude = self.data['latitude']

    def create_time_chart(self):
        # Create figure with two y-axes
        fig = px.line(title='')
        time_interval = pd.to_datetime(self.time, format='%d.%m.%Y %H:%M:%S').to_pydatetime()
        minT = min(time_interval) - timedelta(minutes=2)
        maxT = max(time_interval) + timedelta(minutes=2)
        minT = minT.strftime(format='%Y-%m-%d %H:%M:%S')
        maxT = maxT.strftime(format='%Y-%m-%d %H:%M:%S')

        # Add Depth vs Time (Secondary Y-Axis)
        depths = [-x for x in self.depth]
        # depths = pile_info["Strokes"]
        depth_min = min(depths)
        depth_max = max(depths) + 5
        depth_range = [depth_min, depth_max]

        add_strokes = False
        if sum(self.strokes) != 0:
            add_strokes = True

            strokes_min = min(self.strokes)
            strokes_max = max(self.strokes) + 5
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
            tickformat="%H:%M",  # Format: Hours:Minutes:Seconds
        )

        if add_strokes:
            # Add Strokes vs Time (Primary Y-Axis)
            fig.add_scatter(
                x=time_interval,
                y=self.strokes,
                mode="lines",
                name="Strokes",
                yaxis="y2",
                line=dict(color="green", width=3),
            )

        # Update layout for dual y-axes and dark background
        fig.update_layout(
            margin=dict(b=100),
            yaxis=dict(title="Depth", zerolinecolor='black', side="left", showgrid=True, linecolor='black',
                       gridcolor='rgba(100,100,100,0.5)', mirror=True,
                       minor=dict(showgrid=True, gridcolor='rgba(100,100,100,0.5)', griddash='dot'), range=depth_range),
            #
            xaxis=dict(title="Time", zerolinecolor='black', showgrid=True, linecolor='black', mirror=True,
                       gridcolor='rgba(100,100,100,0.5)',
                       minor=dict(showgrid=True, gridcolor='rgba(100,100,100,0.5)', griddash='dot')),

            plot_bgcolor="#193153",
            paper_bgcolor="#193153",
            font=dict(color="white"),
            xaxis_range=[minT, maxT],
            yaxis_range=[depth_min, depth_max],
            # yaxis2_range= [min(pile_info['Strokes']) - 5, max(pile_info['Strokes']) + 5],
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.3,  # position below the plot
                xanchor="center",
                x=0.5,
                # bgcolor="rgba(0,0,0,0.5)",  # semi-transparent background
                font=dict(size=12),  # adjust font size
                itemwidth=30,  # control item width
            )

        )
        if add_strokes:
            fig.update_layout(
                yaxis2=dict(title="Strokes", zerolinecolor="#193153", overlaying="y", side="right", showgrid=False,
                            linecolor='black', position=1, range=strokes_range))

        fig.update_layout(autosize=False, height=300)

        return fig

    def create_depth_chart(self):

        # Create figure with two y-axes
        # fig1 = px.line(title=f"JobID {selected_jobid} - PileID {selected_pileid} on {selected_date}")
        minD = min(self.depth) - 5
        maxD = max(self.depth) + 5
        # ================================================================================
        # Create subplots with shared y-axis
        fig1 = make_subplots(rows=1, cols=5, shared_yaxes=True, subplot_titles=("Penetration<br>Rate",
                                                                                "Rotary<br>Pressure", "Pulldown",
                                                                                "Rotation", "Volume"))

        # Add traces
        increasing_PR, increasing_D, decreasing_PR, decreasing_D = indrease_decrease_split(
            self.penetration_rate[1:], self.depth[1:])
        # increasing_PR = [-x for x in increasing_PR]
        decreasing_PR = [-x for x in decreasing_PR]
        fig1.add_trace(
            go.Scatter(x=increasing_PR, y=increasing_D, mode='lines', line=dict(color='red', width=2), name='UP'),
            row=1, col=1)
        fig1.add_trace(
            go.Scatter(x=decreasing_PR, y=decreasing_D, mode='lines', line=dict(color='blue', width=2), name='DOWN'),
            row=1, col=1)
        # fig1.add_trace(go.Scatter(x=pile_info["PenetrationRate"], y=pile_info["Depth"], mode='lines', name='PenetrationRate'), row=1, col=1)
        increasing_RP, increasing_D, decreasing_RP, decreasing_D = indrease_decrease_split(
            self.pressure[1:], self.depth[1:])
        fig1.add_trace(go.Scatter(x=increasing_RP, y=increasing_D, mode='lines', line=dict(color='red', width=2),
                                  showlegend=False), row=1, col=2)
        fig1.add_trace(go.Scatter(x=decreasing_RP, y=decreasing_D, mode='lines', line=dict(color='blue', width=2),
                                  showlegend=False), row=1, col=2)
        # fig1.add_trace(go.Scatter(x=pile_info['RotaryHeadPressure'], y=pile_info["Depth"], mode='lines', name='RotaryHeadPressure'), row=1, col=2)
        increasing_Pull, increasing_D, decreasing_Pull, decreasing_D = indrease_decrease_split(
            self.pulldown[1:], self.depth[1:])
        fig1.add_trace(go.Scatter(x=increasing_Pull, y=increasing_D, mode='lines', line=dict(color='red', width=2),
                                  showlegend=False), row=1, col=3)
        fig1.add_trace(go.Scatter(x=decreasing_Pull, y=decreasing_D, mode='lines', line=dict(color='blue', width=2),
                                  showlegend=False), row=1, col=3)
        # fig1.add_trace(go.Scatter(x=pile_info['Pulldown'], y=pile_info["Depth"], mode='lines', name='Pulldown'), row=1, col=3)
        increasing_Rot, increasing_D, decreasing_Rot, decreasing_D = indrease_decrease_split(self.rotation[1:],
                                                                                             self.depth[1:])
        fig1.add_trace(go.Scatter(x=increasing_Rot, y=increasing_D, mode='lines', line=dict(color='red', width=2),
                                  showlegend=False), row=1, col=4)
        fig1.add_trace(go.Scatter(x=decreasing_Rot, y=decreasing_D, mode='lines', line=dict(color='blue', width=2),
                                  showlegend=False), row=1, col=4)
        # fig1.add_trace(go.Scatter(x=pile_info['Rotation'], y=pile_info["Depth"], mode='lines', name='Rotation'), row=1, col=4)
        fig1.add_trace(go.Scatter(x=self.volume[1:], y=self.depth[1:], name='Actual', mode='lines',
                                  line=dict(color='#F6BE00', width=2), showlegend=True), row=1, col=5)
        if not self.diameter is None:
            feet2inch = 12
            minDepth = float(min(self.depth[1:]))
            if self.diameter > 3:
                useDiameter = self.diameter
            else:
                useDiameter = self.diameter * feet2inch
            volume_cy = cylinder_volume_cy(useDiameter, -minDepth)
            fig1.add_trace(go.Scatter(x=[volume_cy, 0], y=[0, minDepth], mode='lines', name='Theoretical',
                                      line=dict(color='grey', width=2, dash='dashdot'), showlegend=True), row=1, col=5)
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
        tils = ['(ft/min)', '(bar)', '(tons)', '(rpm)', '(yd^3)']
        for i in range(0, 5):
            fig1.update_xaxes(title_text=tils[i], row=1, col=i + 1)

        # Configure gridlines for each subplot
        for i in range(0, 5):
            fig1.update_xaxes(
                zerolinecolor='black',
                gridcolor='rgba(100,100,100,0.5)',
                gridwidth=1,
                showgrid=True,
                linecolor='black',
                mirror=True,
                minor=dict(showgrid=True, gridcolor='rgba(100,100,100,0.5)', griddash='dot'),
                row=1,
                col=i + 1
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
                col=i + 1
            )

        # fig1.update_layout(
        #     autosize=True,
        #     margin=dict(l=20, r=20, b=20, t=30),
        # )
        fig1.update_layout(autosize=False, height=600)

        return fig1

    def generate_mwd_pdf(self):
        # Get absolute path to templates/assets
        time_fig = self.create_time_chart()
        depth_fig = self.create_depth_chart()

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

        depth_img = BytesIO()
        # go.Figure(depth_fig).write_image(depth_img, format='png', scale=2)
        # 4x resolution
        go.Figure(depth_fig).write_image(depth_img,scale=4)
        depth_img.seek(0)


        # Create content
        story = []
        LOGO_PATH = assets_path + '/MSB.logo.JPG'
        # Morris Shea Bridge Company
        # DeWaal Pile Drill Log
        jobid = self.job_id
        jobname = self.job_name
        header_table = Table(
            [
                [Paragraph(
                    "Morris Shea Bridge Company<br/>"+
                    str(jobid)+"-" +str(jobname)+"<br/>"
                    "DeWaal Pile Drill Log",
                    title_style
                ),
                    # Paragraph("Morris Shea Pile Drill Log", title_style),
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
        date_drill = pd.to_datetime(self.datetime_array[0]).date().strftime(format='%Y-%m-%d')

        jobname = self.job_name
        client = self.client.lower()
        job_data = [
            ["JOB #:",str(jobid)],
            ["JOBNAME", jobname],
            ["CLIENT:", client],
            ["CONTRACTOR:", "Morris Shea Bridge"],
            ["DATE:", date_drill],

        ]

        # Pile Data
        pile_data = [
            ["PILE No:", f"{self.pile_id}"],
            ["START TIME:", self.drillStartTime],
            ["END TIME:", self.drillEndTime],
            ["INSTALL TIME:", f"{str(self.installTime)}  min"],
            ["RIG:", str(self.rig)],
            # ["OPERATOR:", selected_row.get('OPERATOR', '')],

        ]

        diameter = float(self.diameter)
        if diameter<3:
            covertFeet2inch = 12
        else:
            covertFeet2inch = 1
        try:
            diameter = str(round(float(self.diameter)*covertFeet2inch,2))
        except:
            diameter = str(self.diameter)
        maxstrokes = str(round(float(max(self.strokes[1:])), 0))
        pile_data_2 = [["PILE LENGTH:", str(round(float(self.length),1))+' [ft]'],
            ["PILE DIAMETER:", diameter +' [in]'],
            ["MAXSTROKE:", str(maxstrokes)],
            ["PUMP CALIB.:", str(round(float(self.calibration),3))+' [cy/str]'],
            ["OVER BREAK:", str(self.overbreak)]]

        maxdepth = str(round(float(min(self.depth[1:])),0))
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

        return story

class CPT_Pile():

    def __init__(self, pile_data: Dict,data):
        self.data = pile_data
        self.pile_id = self.data['HoleID']
        self.job_id_cpt = self.data['JobNumber']
        self.date = self.data['Date']
        self.operator = self.data['Operator']
        self.location_id = self.data['LocationID']
        self.total_depth = self.data['Total Depth (feet)']
        self.tip_elevation = self.data['Tip elevation (feet)']
        self.water_table = self.data['Water_Table (feet)']
        self.comments = self.data['Comments']
        self.p1_diameter = self.data['P1_dia (inch)']
        self.add_data(data)

    def add_data(self,data):
        self.depth = data['Depth (feet)']
        self.elevation = data['Elevation (feet)']
        self.q_c = data['q_c (tsf)']
        self.q_t = data['q_t (tsf)']
        self.f_s = data['f_s (tsf)']
        self.u2 = data['U_2 (ft-head)']
        self.u0= data['U_0 (ft-head)']
        self.R_f = data['R_f (%)']
        self.zone_icn = data['Zone_Icn']
        self.sbt = data['Zone_Icn']
        self.b_q = data['B_q']
        self.f_r = data['F_r']
        self.Ic = data['Ic']
        self.Q_t = data['Q_t']
        self.Q_tn = data['Q_tn']
        self.Q_s = data['Q_s (Tons)']
        self.Q_b = data['Q_b (Tons)']
        self.Q_u = data['Q_ult (Tons)']





class Job:
    def __init__(self, job_data: Dict):
        self.job_id = job_data.get('JobID', '')
        self.job_name = job_data.get('jobName', '')
        self.location = job_data.get('locality', '')
        self.longitude = job_data.get('longitude', '')
        self.latitude = job_data.get('latitude', '')
        self.description = job_data.get('description', '')
        self.piles = {}
        self.cpt_piles = {}
        self.estimate_labourHours = 0
        self.estimate_rig_days = 0
        self.estimate_piles = 0
        self.estimate_concrete = 0
        self.estimate_piles_per_day = 0
        self.estimate_concrete_per_day = 0
        self.estimate_manhours_per_day = 0
        self.estimate_piles_per_piletype = {}
        self.piles_per_date ={}
        self.pile_schedule = pd.DataFrame()
        self.colorCodes ={}
        self.design_markers ={}
        self.daily_stats = {}
        self.job2data_stats = {}
        self.job2data_stats_complete = {}
        self.piles_details = None
        self.piles_timeseries = None
        self.start_date = None
        self.last_date = None
        self.df_expected = pd.DataFrame()

    def add_stats_files(self,stats):
        if isinstance(stats, list):
            stats = stats[0]
        self.daily_stats = pd.DataFrame.from_records(stats.get("DailyStatistics", {}))
        self.job2data_stats_complete = stats.get('JobToDateStatistics', {})

        if len(self.job2data_stats_complete)>0 and self.estimate_piles>0:
            self.job2data_stats_complete = pd.DataFrame.from_records(self.job2data_stats_complete)
            self.job2data_stats_complete['Time'] = pd.to_datetime(self.job2data_stats_complete['Time']).dt.date

            df_todate = self.job2data_stats_complete.copy()

            df_todate['ConcreteDelivered'] = pd.to_numeric(df_todate['ConcreteDelivered'])
            df_todate['LaborHours'] = pd.to_numeric(df_todate['LaborHours'])
            df_todate['DaysRigDrilled'] = pd.to_numeric(df_todate['DaysRigDrilled'])

            df_todate_tot = df_todate.groupby('Time').sum(numeric_only=True)
            df_todate_tot['Piles%'] = df_todate_tot['Piles'] / self.estimate_piles
            df_todate_tot['Concrete%'] = df_todate_tot['ConcreteDelivered'] / self.estimate_concrete
            df_todate_tot['RigDays%'] = df_todate_tot['DaysRigDrilled'] / self.estimate_rig_days
            df_todate_tot['LaborHours%'] = df_todate_tot['LaborHours'] / self.estimate_labourHours
            # df_todate_tot['Delta_Piles_vs_Concrete'] = df_todate_tot['Piles%'] - df_todate_tot['Concrete%']
            # df_todate_tot['Delta_Piles_vs_RigDays'] = df_todate_tot['Piles%'] - df_todate_tot['RigDays%']
            # df_todate_tot['Delta_Piles_vs_Labor Hours'] = df_todate_tot['Piles%'] - df_todate_tot['LaborHours%']
            # df_todate_tot['Delta_Piles_vs_Concrete_prev'] = df_todate_tot['Delta_Piles_vs_Concrete'].shift(1)
            # df_todate_tot['Delta_Piles_vs_RigDays_prev'] = df_todate_tot['Delta_Piles_vs_RigDays'].shift(1)
            # df_todate_tot['Delta_Piles_vs_Labor Hours_prev'] = df_todate_tot['Delta_Piles_vs_Labor Hours'].shift(1)

            self.job2data_stats = df_todate_tot.reset_index()

    def add_piles_details(self,df:pd.DataFrame,df_ts:pd.DataFrame()):
        self.piles_details = df
        self.piles_details[self.piles_details['longitude'].isnull()] == self.longitude
        self.piles_details[self.piles_details['latitude'].isnull()] == self.latitude
        self.piles_timeseries = df_ts
        self.piles_details['date'] = pd.to_datetime(self.piles_details['date'])
        self.start_date = min(self.piles_details[self.piles_details['PileCode']=='Production Pile']['date'])
        self.last_date = max(self.piles_details[self.piles_details['PileCode'] == 'Production Pile']['date'])
        self.df_expected = self._calculate_expected_progress_with_holidays()


    def _calculate_expected_progress_with_holidays(self):
        dates = []
        expected_piles = []
        expected_concrete = []
        expected_labour = []
        current_date = self.start_date
        cumulative_piles = 0
        cumulative_concrete = 0
        cumulative_labour = 0

        # Ensure start date is a working day
        while not is_working_day(current_date):
            current_date = next_working_day(current_date)

        while cumulative_piles < self.estimate_piles:
            dates.append(current_date)
            cumulative_piles = min(cumulative_piles + self.estimate_piles_per_day, self.estimate_piles)
            cumulative_concrete = min(cumulative_concrete+self.estimate_concrete_per_day,self.estimate_concrete)
            cumulative_labour = min(cumulative_labour+self.estimate_manhours_per_day,self.estimate_labourHours)
            expected_piles.append(cumulative_piles)
            expected_concrete.append(cumulative_concrete)
            expected_labour.append(cumulative_labour)
            current_date = next_working_day(current_date)


        return pd.DataFrame({
            'date': dates,
            'expected_piles': expected_piles,
            'expected_concrete': expected_concrete,
            'expected_labour': expected_labour
        })
    def add_colorCodes(self,job_data):
        for k, v in job_data.items():
            if not v is None:
                self.colorCodes[k] = v.get('colorCode','')

    def add_estimates(self,job_data):
        for k, v in job_data.items():
            if not v is None:
                self.estimate_labourHours += v.get('manHoursNeeded', 0)
                self.estimate_rig_days += v.get('rigDays', 0)
                self.estimate_piles += v.get('contract', 0)
                self.estimate_piles_per_day += v.get('pilesPerDay',0)*v.get('contract', 0)
                self.estimate_manhours_per_day += v.get('manHoursPerPile',0)*v.get('pilesPerDay',0)*v.get('contract', 0)
                self.estimate_piles_per_piletype[k] = v.get('contract', 0)
                diameter = v.get('diameter', 0)
                length = v.get('averageLength', 0)
                volume = cylinder_volume_cy(diameter, length)
                pile_waste = v.get('pileWaste', 0)
                estimate_concrete = v.get('totalConcreteVolume',0)
                if estimate_concrete is None:
                    estimate_concrete = v.get('contract', 0)*volume*(1+pile_waste)
                self.estimate_concrete += estimate_concrete
                self.estimate_concrete_per_day += v.get('pilesPerDay',0)*volume*(1+pile_waste)*v.get('contract', 0)

        if self.estimate_piles>0:

            self.estimate_piles_per_day = self.estimate_piles_per_day/self.estimate_piles
            self.estimate_concrete_per_day = self.estimate_concrete_per_day/self.estimate_piles
            self.estimate_manhours_per_day = self.estimate_manhours_per_day//self.estimate_piles

    def add_pile(self, pileid:str, basedata, pile_time_data):
        # if pileid not in self.piles:
        self.piles[pileid] = Pile(basedata, pile_time_data)

    def add_pile_schedule(self,df:pd.DataFrame):
        self.pile_schedule = df
    def add_design_markers(self,markers:Dict):
        self.design_markers = markers

    def add_cpt_pile(self,pileid,header_data:Dict,data):
        self.cpt_piles[pileid] = CPT_Pile(header_data,data)


    def get_piles_per_date(self):
        for id, pile in self.piles.items():
            date = pd.to_datetime(pile.time).date()
            if date in self.piles_per_date:
                self.piles_per_date[date].apped(id)
            else:
                self.piles_per_date[date] = [id]


    def generate_daily_summary_pdf(self):

        if len(self.daily_stats)>0:
            self.daily_stats['Time'] = pd.to_datetime(self.daily_stats['Time']).dt.date
            unique_dates = list(self.daily_stats['Time'].unique())
            for d in unique_dates:
                mdate = d.strftime('%Y-%m-%d')
                filename = f"{self.job_id}_Daily_Report_{mdate}.pdf"
                filename_path = os.path.join(assets_path, 'daily_reports', filename)
                if not os.path.isfile(filename_path):
                    self._create_daily_report(d,filename_path)

    def _create_daily_report(self,mdate,filename):

        data = self.daily_stats[self.daily_stats['Time'] == mdate]
        data2date = self.job2data_stats_complete[self.job2data_stats_complete['Time'] == mdate]
        pile_data_full = self.piles_details[pd.to_datetime(self.piles_details['date']).dt.date == mdate]


        doc = SimpleDocTemplate(filename, pagesize=letter,
                                leftMargin=0.5 * inch,
                                rightMargin=0.5 * inch,
                                topMargin=0.5 * inch,
                                bottomMargin=0.5 * inch)

        # Define portrait frame
        portrait_frame = Frame(
            doc.leftMargin, doc.bottomMargin,
            doc.width, doc.height,
            id='portrait'
        )

        # Define landscape frame
        landscape_frame = Frame(
            doc.leftMargin, doc.bottomMargin,
            landscape(letter)[0] - doc.leftMargin - doc.rightMargin,
            landscape(letter)[1] - doc.topMargin - doc.bottomMargin,
            id='landscape'
        )

        # Add templates
        doc.addPageTemplates([
            PageTemplate(id='portrait', frames=[portrait_frame], pagesize=letter),
            PageTemplate(id='landscape', frames=[landscape_frame], pagesize=landscape(letter)),
        ])

        styles = getSampleStyleSheet()

        title_background_color = colors.navy
        title_text_color = colors.white

        # Custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=14,
            leading=16,
            spaceAfter=12,
            alignment=TA_LEFT,

        )

        # Create a style for wrapped header text
        header_cell_style = ParagraphStyle(
            'HeaderCell',
            parent=styles['Normal'],
            fontSize=7,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            textColor = title_text_color
        )

        # Create content
        story = []
        LOGO_PATH = assets_path + '/MSB.logo.JPG'
        logo =Image(LOGO_PATH, width=1 * inch, height=0.75 * inch) if os.path.exists(LOGO_PATH) else Spacer(1, 1)
        header_table = Table(
            [
                [Paragraph(
                    "Daily Report: " + mdate.strftime('%Y-%m-%d') + "<br/>" +
                    str(self.job_id) + "-" + str(self.job_name) + "<br/>" +
                    self.location,
                    title_style
                ),
                    logo
                ]
            ],
            colWidths=[6.0 * inch, 1.5 * inch]  # Adjust width as needed
        )

        header_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))

        story.append(header_table)

        section_style = ParagraphStyle(
            'CustomSection',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            alignment=TA_LEFT
        )

        # Calculate available width for tables
        available_width = 7.5 * inch  # Letter width (8.5") minus margins (0.5" each side)

        # Add Rig Summary section
        story.append(Spacer(1, 12))
        story.append(Paragraph("Rig Summary", section_style))

        # Create Rig Summary table with wrapped headers
        rig_summary_headers = [
            Paragraph('RIGID', header_cell_style),
            Paragraph('PILES', header_cell_style),
            Paragraph('AVG<br/>LENGTH', header_cell_style),
            Paragraph('CONCRETE<br/>yd3', header_cell_style),
            Paragraph('PILE<br/>WASTE', header_cell_style),
            Paragraph('RIG<br/>WASTE', header_cell_style),
            Paragraph('CYCLE<br/>TIME', header_cell_style),
            Paragraph('DELAY<br/>TIME', header_cell_style),
            Paragraph('SHIFT START<br/>TIME', header_cell_style),
            Paragraph('SHIFT END<br/>TIME', header_cell_style),
            Paragraph('TURN START<br/>TIME', header_cell_style),
            Paragraph('TURN END<br/>TIME', header_cell_style),
        ]
        # mean_PileLength	ConcreteDelivered	PileWaste	RigWaste	sum_CycleTime	sum_DelayTime
        rig_summary_data = [rig_summary_headers]
        for i in range(len(data)):
            try:
                start_shift = pd.to_datetime(data["ShiftStartTime"].iloc[i]).time().strftime(format='%H:%M') + ' AM'
                end_shift = pd.to_datetime(data["ShiftEndTime"].iloc[i]).time().strftime(format='%H:%M') + ' PM'
            except:
                start_shift = None
                end_shift = None
            rig_summary_data.append(
                [data["RigID"].iloc[i],
                 data["Piles"].iloc[i],
                 round(float(data["mean_PileLength"].iloc[i]),0),
                 round(float(data["ConcreteDelivered"].iloc[i]),0),
                 round(float(data["PileWaste"].iloc[i]),1),
                 round(float(data["RigWaste"].iloc[i]),1),
                 format_time_to_hours_minutes(data["sum_CycleTime"].iloc[i]),
                 format_time_to_hours_minutes(data["sum_DelayTime"].iloc[i]),
                 start_shift,
                 end_shift,
                 format_time_to_hours_minutes(data["TurnStartTime"].iloc[i]),
                 format_time_to_hours_minutes(data["TurnEndTime"].iloc[i]),
                 ])


        # Calculate column widths for rig summary table
        num_cols = len(rig_summary_headers)
        col_width = available_width / num_cols

        rig_summary_table = Table(rig_summary_data,
                                  colWidths=[col_width] * num_cols)

        rig_summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), title_background_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(rig_summary_table)
        # ==========================================================
        # ==========================================================
        # Add Job to Date section
        story.append(Spacer(1, 24))
        story.append(Paragraph("Job to Date", section_style))
        # data2date

        # Create Job to Date table with wrapped headers
        job_to_date_headers = [
            Paragraph('RIGID', header_cell_style),
            Paragraph('PILES<br/>DRILLED', header_cell_style),
            Paragraph('AVC<br/>LENGTH,<br/>(ft)', header_cell_style),
            Paragraph('CONCRETE<br/>yd3', header_cell_style),
            Paragraph('PILE<br/>WASTE', header_cell_style),
            Paragraph('RIG<br/>WASTE', header_cell_style),
            Paragraph('HOURS<br/>CYCLETIME', header_cell_style),
            Paragraph('HOURS<br/>DELAY', header_cell_style),
            Paragraph('DAYS<br/>DRILLED', header_cell_style),
            Paragraph('LABOUR<br/>HOURS', header_cell_style),

        ]
        # MeanCycleTime	HoursDelayed	DaysRigDrilled	LaborHours
        job_to_date_data = [job_to_date_headers]
        for i in range(len(data2date)):
            job_to_date_data.append(
                [data2date["RigID"].iloc[i],
                 data2date["Piles"].iloc[i],
                 round(float(data2date["AveragePileLength"].iloc[i]),0),
                 data2date["ConcreteDelivered"].iloc[i],
                 round(float(data2date["AveragePileWaste"].iloc[i]),0),
                 round(float(data2date["AverageRigWaste"].iloc[i]),0),
                 format_time_to_hours_minutes(data2date["HoursCycle"].iloc[i]),
                 format_time_to_hours_minutes(data2date["HoursDelayed"].iloc[i]),
                 data2date["DaysRigDrilled"].iloc[i],
                 data2date["LaborHours"].iloc[i]
            ])

        # Calculate column widths for job to date table
        num_cols_jtd = len(job_to_date_headers)
        col_width_jtd = available_width / num_cols_jtd

        job_to_date_table = Table(job_to_date_data,
                                  colWidths=[col_width_jtd] * num_cols_jtd)

        job_to_date_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), title_background_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(job_to_date_table)
        # ==========================================================
        # Loop throughRigID
        rig_ids = pile_data_full['RigID'].unique()
        for rigid in rig_ids:
            # Add page break for Daily Pile Log and switch to landscape
            story.append(NextPageTemplate('landscape'))
            story.append(PageBreak())
            pile_data = pile_data_full[pile_data_full['RigID']==rigid]
            # Calculate total piles for the day
            total_piles = len(pile_data) if not pile_data.empty else 0
            # Get pump ID from data
            pump_id = str(pile_data['PumpID'].iloc[0])
            pump_calibration = pile_data['PumpCalibration'].iloc[0]
            pump_calibration = round(float(pump_calibration),2) if not pump_calibration is None else 0

            styles = getSampleStyleSheet()
            normal = styles["Normal"]

            # Left side text
            left_text = "<para align=left><font size=14><b>Daily Pile Report -" + mdate.strftime('%a, %m/%d/%y') + ", Rig "+ rigid + "</b></font><br/>  <font size=9>Job "+ self.job_id+"-"+ self.job_name + "<br/>" + self.location + "</font></para>"
            left_para = Paragraph(left_text, normal)
            # Right side text (pump + diameter above logo + pile count below)
            rigth_text_style = ParagraphStyle(
                'CustomSection',
                parent=styles['Normal'],
                fontSize=9,
                spaceAfter=12,
                alignment=TA_LEFT
            )
            right_text = "PumpID:"+ pump_id +"<br/>Calibration: "+str(pump_calibration)
            pump_para = Paragraph(right_text, rigth_text_style)

            pump_logo_table = Table([[pump_para, logo]], colWidths=[80, 100])
            pump_logo_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "RIGHT"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ]))
            # Pile count under logo
            pile_text = Paragraph("<para align=center><b> PILES:"+ str(total_piles)+"</b></para>", normal)

            # Assemble right column vertically
            right_table = Table([[pump_logo_table],
                               [pile_text]],
                              colWidths=[180])
            right_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]))
            # Calculate available width in landscape
            landscape_width, _ = landscape(letter)
            available_width = landscape_width - (doc.leftMargin + doc.rightMargin)

            # e.g. 70% for left, 30% for right
            left_width = 0.7 * available_width
            right_width = 0.3 * available_width

            daily_pile_header_table = Table(
                [[left_para, right_table]],
                colWidths=[left_width, right_width]
            )
            # Final header table (left + right)
            # daily_pile_header_table = Table([[left_para, right_table]], colWidths=[350, 180])
            daily_pile_header_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 1, colors.black),  # only outer border
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(daily_pile_header_table)
            story.append(Spacer(1, 24))

            # Create table with wrapped headers
            daily_piles_headers = [
                Paragraph('RIGID', header_cell_style),
                Paragraph('INSTALL<br/> START TIME', header_cell_style),
                Paragraph('PILEID', header_cell_style),
                Paragraph('PILE<br/>TYPE', header_cell_style),
                Paragraph('MOVE<br/>TIME', header_cell_style),
                Paragraph('INSTALL<br/>TIME', header_cell_style),
                Paragraph('CYCLE<br/>TIME', header_cell_style),
                Paragraph('DELAY<br/>TIME', header_cell_style),
                Paragraph('PILE<br/>LENGTH<br/>(ft)', header_cell_style),
                Paragraph('MAX<br/>STROKE', header_cell_style),
                Paragraph('OVER<br/>BREAK', header_cell_style),
                Paragraph('LON/LAT', header_cell_style),
                Paragraph('COMMENTS', header_cell_style),

            ]
            daily_piles_data = [daily_piles_headers]
            pile_data['InstallStartTime'] = pd.to_datetime(pile_data['InstallStartTime'])
            pile_data.sort_values(by='InstallStartTime',inplace=True)
            cycletime_sum = 0
            overbreak_mean = 0
            for i in range(len(pile_data)):
                try:
                    install_start = pd.to_datetime((pile_data['InstallStartTime'].iloc[i])).time().strftime(format='%H:%M')
                except:
                    install_start = None
                cycletime = pile_data["CycleTime"].iloc[i] if not pile_data["CycleTime"].iloc[i]  is None else 0
                cycletime = round(float(str(cycletime).split(' ')[0]),1)
                cycletime_sum += cycletime
                overbreak = pile_data["OverBreak"].iloc[i] if not pile_data["OverBreak"].iloc[i] is None else '0%'
                overbreak_mean += float(overbreak.split('%')[0])
                lon_lat = True if not pile_data['latitude'].iloc[i] is None else False
                daily_piles_data.append(
                    [pile_data["RigID"].iloc[i],
                     install_start,
                     pile_data["PileID"].iloc[i],
                     pile_data["PileType"].iloc[i],
                     format_time_to_hours_minutes(pile_data["MoveTime"].iloc[i]),
                     format_time_to_hours_minutes(pile_data["InstallTime"].iloc[i]),
                     cycletime,
                     format_time_to_hours_minutes(pile_data["DelayTime"].iloc[i]),
                     pile_data["PileLength"].iloc[i],
                     pile_data["MaxStroke"].iloc[i],
                     overbreak,
                     lon_lat,
                     pile_data["Comments"].iloc[i],
                     ])
            # now append the totals
            daily_piles_data.append(['Total by Rig',
                     '',
                     '',
                     '',
                     round(pile_data["MoveTime"].sum(),0),
                     round(pile_data["InstallTime"].sum(),0),
                     cycletime_sum,
                     round(pile_data["DelayTime"].sum(),0),
                     round(pile_data["PileLength"].sum(),1),
                     round(pile_data["MaxStroke"].mean(),0),
                     f"{str(round(overbreak_mean/len(pile_data),1))}%",
                     '',
                     '',
                     ])
            # Calculate column widths for job to date table
            num_cols_jtd = len(daily_piles_headers)
            # landscape_width, _ = landscape(letter)
            # available_width = landscape_width - (doc.leftMargin + doc.rightMargin)
            # Let’s make comments column take ~25% of width
            comment_col_index = num_cols_jtd - 1
            comment_width = 0.25 * available_width

            # Remaining width distributed across other columns
            other_width = (available_width - comment_width) / (num_cols_jtd - 1)
            col_widths = [other_width] * num_cols_jtd
            col_widths[comment_col_index] = comment_width

            daily_piles_table = Table(daily_piles_data, colWidths=col_widths)


            daily_piles_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), title_background_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(daily_piles_table)
            # ==========================================================
            # add charts by Pile
            for row in pile_data.itertuples():
                # After table, switch back to portrait
                story.append(NextPageTemplate('portrait'))
                story.append(PageBreak())
                pileid = row.PileID
                try:
                    day_data = self.piles_timeseries[pileid][mdate.strftime('%Y-%m-%d')]
                except:
                    continue
                if len(day_data)>0:
                    self.add_pile(pileid,row,self.piles_timeseries[pileid][mdate.strftime('%Y-%m-%d')])
                    mwd_story = self.piles[pileid].generate_mwd_pdf()
                    story.extend(mwd_story)
                else:
                    print('Data not available')


        #

        # Generate PDF
        doc.build(story)




    def plot_all_piles(self, save_path: Optional[str] = None):
        for pile in self.piles:
            pile.plot_pile_data(save_path)


class JobManager:
    def __init__(self):
        self.jobs = {}

    def get_job(self,jobid):
        if jobid in self.jobs:
            return self.jobs[jobid]

    def add_job(self, job_data: Dict):
        job_id = job_data.get('JobID', '')
        if job_id not in self.jobs:
            self.jobs[job_id] = Job(job_data)
            return self.jobs[job_id]
        else:
            return None

    def load_from_json(self, json_data: Dict):
        for feature in json_data['features']:
            job_id = feature['properties']['JobID']
            job_data = {
                'JobID': job_id,
                'JobName': feature['properties']['JobName'],
                'Location': feature['properties']['Location'],
            }

            job = self.add_job(job_data)
            job.add_pile(feature)

