import json
import pandas as pd
from datetime import datetime,timedelta
from typing import List, Dict, Optional
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# from functions import indrease_decrease_split,cylinder_volume_cy
import math
columns_cpt = ['Depth (feet)','Elevation (feet)','q_c (tsf)','q_t (tsf)','f_s (tsf)','U_2 (ft-head)','U_0 (ft-head)','R_f (%)','Zone_Icn','SBT_Icn','B_q','F_r','Q_t','Ic','Q_tn','Q_s (Tons)','Q_b (Tons)','Q_ult (Tons)']
name_cpt_file_header = 'CPT-online-header.csv'

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

class Pile:
    def __init__(self, data,pile_data):
        # self.data = pile_data['properties']
        self.data = data
        self.pile_id = self.data.PileID
        self.job_id = self.data.JobID

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
            self.datetime = [datetime.strptime(t, "%d.%m.%Y %H:%M:%S") for t in self.time]
        except:
            self.datetime = [datetime.strptime(t, "%Y-%m-%d %H:%M:%S") for t in self.time]
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
        self.job_name = job_data.get('title', '')
        self.location = job_data.get('locality', '')
        self.longitude = job_data.get('longitude', '')
        self.latitude = job_data.get('latitude', '')
        self.piles = {}
        self.cpt_piles = {}
        self.estimate_labourHours = 0
        self.estimate_rig_days = 0
        self.estimate_piles = 0
        self.estimate_concrete = 0
        self.piles_per_date ={}

    def add_estimates(self,job_data):
        for k, v in job_data.items():
            self.estimate_labourHours += v.get('manHoursNeeded', 0)
            self.estimate_rig_days += v.get('rigDays', 0)
            self.estimate_piles += v.get('contract', 0)

            estimate_concrete = v.get('totalConcreteVolume',0)
            if estimate_concrete is None:
                diameter = v.get('diameter', 0)
                length = v.get('averageLength', 0)
                volume = cylinder_volume_cy(diameter, length)
                pile_waste = v.get('pileWaste', 0)
                estimate_concrete = v.get('contract', 0)*volume*(1+pile_waste)

            self.estimate_concrete += estimate_concrete

    def add_pile(self, pileid:str, data, pile_data):
        # if pileid not in self.piles:
        self.piles[pileid] = Pile(data, pile_data)

    def add_cpt_pile(self,pileid,header_data:Dict,data):
        self.cpt_piles[pileid] = CPT_Pile(header_data,data)


    def get_piles_per_date(self):
        for id, pile in self.piles.items():
            date = pd.to_datetime(pile.time).date()
            if date in self.piles_per_date:
                self.piles_per_date[date].apped(id)
            else:
                self.piles_per_date[date] = [id]


    def generate_summary(self) -> Dict:
        summary = {
            'Job ID': self.job_id,
            'Job Name': self.job_name,
            'Number of Piles': len(self.piles),
            'Total Man Hours': self.man_hours,
            'Total Rig Days': self.rig_days,

        }


        return summary

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


        # def generate_all_summaries(self) -> pd.DataFrame:
        #     summaries = []
        #     for job in self.jobs.values():
        #         summaries.append(job.generate_summary())
        #     return pd.DataFrame(summaries)
        #
        # def plot_all_jobs(self, save_dir: str):
        #     os.makedirs(save_dir, exist_ok=True)
        #     for job in self.jobs.values():
        #         job.plot_all_piles(save_dir)