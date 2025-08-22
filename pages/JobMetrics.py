
from dash import dcc, html, Output, Input, State, callback,no_update,ctx
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from dash.exceptions import PreventUpdate
import numpy as np
import pandas as pd
import os
import dash
import dash_ag_grid as dag
from datetime import date
from functions import result_MWD,cache_manager
import dash_bootstrap_components as dbc


dash.register_page(
    __name__,
    path_template="/Metrics",
    path="/Metrics",
)

assets_path = os.path.join(os.getcwd(), "assets")
summary_folder = os.path.join(assets_path, 'data','Summary')
# Initialize cache manager
# from cache_manager import ChartDataCache
# cache_manager = ChartDataCache(result_MWD)
def count_piles_for_date(data, target_date):
    return sum(1 for pile_data in data.values() if target_date in pile_data)


from collections import defaultdict


def count_piles_per_date(data):
    date_counts = defaultdict(int)

    for pile_data in data.values():  # Loop through each nested dict
        for date in pile_data:  # Extract each date in the nested dict
            date_counts[date] += 1  # Increment count for that date
    # Convert to DataFrame
    df = pd.DataFrame(list(date_counts.items()), columns=['Date', 'PileCount'])
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')  # Optional: Sort by date
    return df

    return dict(date_counts)  # Convert to a regular dict for cleaner output
def load_data():
    summary_dict_to_date = {}
    summary_dict_daily = {}
    summary_design = {}
    summary_metrics ={}
    summary_metrics_daily = {}
    jobs = []
    for f in os.listdir(summary_folder):
        jobnumber = None
        jobnumber_design = None
        if 'ESTIMATE' in f:
            jobnumber_design = int(f.split('-')[0])
        elif 'SiteProgression' in f:
            jobnumber = int(f.split('-')[0])

        else:
            continue

        if not jobnumber is None:
            if not str(jobnumber) in result_MWD.keys():
                continue
            jobs.append(jobnumber)
            df_todate = pd.read_excel(os.path.join(summary_folder, f), sheet_name='Job To Date')
            df_daily = pd.read_excel(os.path.join(summary_folder, f), sheet_name='Daily')
            df_todate['Time'] = pd.to_datetime(df_todate['Time'])
            df_daily['Time'] = pd.to_datetime(df_daily['Time'])
            summary_dict_to_date[jobnumber] = df_todate
            summary_dict_daily[jobnumber] = df_daily
        if not jobnumber_design is None:
            df_design = pd.read_excel(os.path.join(summary_folder, f))
            summary_design[jobnumber_design] = df_design

    for jb in jobs:
        df_todate = summary_dict_to_date[jb]
        df_design = summary_design[jb]
        if len(df_design)==0:
            continue
        df_todate_tot = df_todate.groupby('Time').sum(numeric_only=True)
        df_design.columns = df_design.columns.str.strip()
        time_interval = pd.to_datetime(df_todate_tot.index)
        df_todate_tot['Piles%'] = df_todate_tot['Piles']/df_design['COUNT'].sum()
        df_todate_tot['Concrete%'] = df_todate_tot['ConcreteDelivered']/df_design['CONCRETE'].sum()
        df_todate_tot['RigDays%'] = df_todate_tot['DaysRigDrilled']/df_design['RIG DAYS'].sum()
        df_todate_tot['LaborHours%'] = df_todate_tot['LaborHours']/df_design['MAN HOURS'].sum()
        df_todate_tot['Delta_Piles_vs_Concrete'] = df_todate_tot['Piles%']-df_todate_tot['Concrete%']
        df_todate_tot['Delta_Piles_vs_RigDays'] = df_todate_tot['Piles%'] - df_todate_tot['RigDays%']
        df_todate_tot['Delta_Piles_vs_Labor Hours'] = df_todate_tot['Piles%'] - df_todate_tot['LaborHours%']
        df_todate_tot['Delta_Piles_vs_Concrete_prev'] = df_todate_tot['Delta_Piles_vs_Concrete'].shift(1)
        df_todate_tot['Delta_Piles_vs_RigDays_prev'] = df_todate_tot['Delta_Piles_vs_RigDays'].shift(1)
        df_todate_tot['Delta_Piles_vs_Labor Hours_prev'] = df_todate_tot['Delta_Piles_vs_Labor Hours'].shift(1)

        summary_metrics[jb] = df_todate_tot.reset_index()

    return summary_metrics,summary_dict_daily


# ======================
# Prepare AG Grid data
# ======================
def prepare_table_data(summary_metrics, selected_date):
    rows = []
    for job, df in summary_metrics.items():
        df_on_date = df[df['Time'] <= selected_date].sort_values('Time')
        if len(df_on_date) < 2:
            continue

        current = df_on_date.iloc[-1]
        previous = df_on_date.iloc[-2]

        def format_delta(curr, prev):
            if pd.isna(curr):
                return "", "black"
            if pd.isna(prev) or curr == prev:
                return f"→ {curr:.1f}%", "black"
            elif curr > prev:
                return f"↑ {curr:.1f}%", "red"  # worse
            else:
                return f"↓ {curr:.1f}%", "green"  # better

        delta_cells = {}
        delta_colors = {}
        for col in ['Delta_Piles_vs_Concrete', 'Delta_Piles_vs_RigDays', 'Delta_Piles_vs_Labor Hours']:
            text, color = format_delta(current[col]*100, previous[col]*100)
            delta_cells[col] = text
            delta_colors[col] = color

        # Status classification
        max_delta = max(abs(current['Delta_Piles_vs_Concrete']),
                        abs(current['Delta_Piles_vs_RigDays']),
                        abs(current['Delta_Piles_vs_Labor Hours']))
        max_delta=abs(max_delta*100)
        if max_delta < 5:
            status = "green"
            status_symbol = "✅"
        elif max_delta <= 10:
            status = "orange"
            status_symbol = "⚠"
        else:
            status = "red"
            status_symbol = "❌"
        piles_per_day = round(current['Piles']/current['DaysRigDrilled'],0)
        rows.append({
            "JobNumber": job,
            "StatusSymbol": status_symbol,
            "StatusColor": status,
            "Piles Drilled":f"{current['Piles']}",
            "Piles %": f"{current['Piles%']*100:.1f}%",
            "Concrete Delivered": f"{current['ConcreteDelivered']}",
            "Concrete %": f"{current['Concrete%']*100:.1f}%",
            "Labor Hours": f"{current['LaborHours']}",
            "Labor Hours %": f"{current['LaborHours%'] * 100:.1f}%",
            "Days Rig Drilled": f"{current['DaysRigDrilled']}",
            "Rig Days %": f"{current['RigDays%']*100:.1f}%",
            "Average Piles/Day":f"{piles_per_day}",
            "AveragePileLength": f"{current['AveragePileLength']:.2f}",
            "Delta_Piles_vs_Concrete": delta_cells['Delta_Piles_vs_Concrete'],
            "Delta_Piles_vs_RigDays": delta_cells['Delta_Piles_vs_RigDays'],
            "Delta_Piles_vs_Labor Hours": delta_cells['Delta_Piles_vs_Labor Hours'],
            "DeltaColors": delta_colors
        })

    return rows




def prepare_table_data_daily(summary_metrics, selected_date):
    rows = []
    total_piles = 0
    total_concrete = 0
    total_rig_days = 0
    total_labor_hours = 0

    for job, df in summary_metrics.items():
        df['Piles_delta'] = df['Piles'].diff()
        df['Concrete_delta'] = df['ConcreteDelivered'].diff()
        df['DaysRig_delta'] = df['DaysRigDrilled'].diff()
        df['ManHours_delta'] = df['LaborHours'].diff()
        df_on_date = df[df['Time'] == selected_date].sort_values('Time')
        if len(df_on_date) == 0:
            continue

        current = df_on_date.iloc[-1]
        # previous = df_on_date.iloc[-2]

        total_piles += current["Piles_delta"]
        total_concrete += current["Concrete_delta"]
        total_rig_days += current["DaysRig_delta"]
        total_labor_hours += current["ManHours_delta"]

    rows = {"Piles":total_piles,"ConcreteDelivered":total_concrete,"DaysRigDrilled":total_rig_days,"LaborHours":total_labor_hours}

    return rows

def prepare_time_spent_stats(summary_dict_daily):

    # cols = ['Time','RigID','Piles','sum_MoveTime','mean_MoveTime','sum_DrillTime','mean_DrillTime','sum_GroutTime','mean_GroutTime',
    #         'sum_InstallTime','mean_InstallTime','sum_DelayTime','mean_DelayTime','sum_CycleTime'	,'mean_CycleTime',
    #         'sum_PileLength','mean_PileLength','mean_OverBreak','sum_GroutVolume','sum_PileVolume',	'TurnTime'	,
    #         'PileWaste'	,'ConcreteDelivered','LaborHours','TurnStartTime','TurnEndTime','ShiftStartTime'	,
    #         'ShiftEndTime',	'ShiftTime','RigWaste','ShiftTime','RigWaste']
    # time_cols = ['sum_MoveTime','mean_MoveTime','sum_DrillTime','mean_DrillTime','sum_GroutTime','mean_GroutTime',
    #         'sum_InstallTime','mean_InstallTime','sum_DelayTime','mean_DelayTime','sum_CycleTime','mean_CycleTime']

    out_df = pd.DataFrame()
    for job, df in summary_dict_daily.items():
        tmp = df[['Time','RigID','Piles']]
        tmp['JobID'] = job
        for name in df.columns:
            if name.startswith('mean_') and name.endswith('Time'):
                name_=name.split('_')[1]
                tmp[name_] = df[name].str.split('min',expand=True)[0]
                tmp[name_] = pd.to_numeric(tmp[name_],errors= 'coerce')

        out_df = pd.concat([out_df,tmp],ignore_index=True)

    return out_df


summary_metrics,summary_dic_daily = load_data()
# table_rows = prepare_table_data(summary_metrics,selected_date)

# ======================
# Dash AG Grid
# ======================
#  "JobNumber": job,
#             "StatusSymbol": status_symbol,
#             "StatusColor": status,
#             "Piles Drilled":f"{current['Piles']}",
#             "Piles %": f"{current['Piles%']*100:.1f}%",
#             "Concrete Delivered": f"{current['ConcreteDelivered']}",
#             "Concrete %": f"{current['Concrete%']*100:.1f}%",
#             "Labor Hours": f"{current['LaborHours']}",
#             "Labor Hours %": f"{current['LaborHours%'] * 100:.1f}%",
#             "Days Rig Drilled": f"{current['DaysRigDrilled']}",
#             "Rig Days %": f"{current['RigDays%']*100:.1f}%",
#             "Average Piles/Day":f"{piles_per_day}",
#             "AveragePileLength": f"{current['AveragePileLength']}",
column_defs = [
    {"headerName": "JobNumber", "field": "JobNumber"},
    {
        "headerName": "Status",
        "field": "StatusSymbol",
        "cellStyle": {
            "function": """
                function(params) {
                    if (params.data.StatusColor === 'green') return {backgroundColor: '#d4edda', textAlign: 'center'};
                    if (params.data.StatusColor === 'orange') return {backgroundColor: '#fff3cd', textAlign: 'center'};
                    if (params.data.StatusColor === 'red') return {backgroundColor: '#f8d7da', textAlign: 'center'};
                    return {textAlign: 'center'};
                }
            """
        }
    },
    {"headerName": "Piles Drilled", "field": "Piles Drilled"},
    {"headerName": "Piles %", "field": "Piles %"},
    {"headerName": "Concrete Delivered", "field": "Concrete Delivered"},
    {"headerName": "Concrete %", "field": "Concrete %"},
    {"headerName": "Labor Hours", "field": "Labor Hours"},
    {"headerName": "Labor Hours", "field": "Labor Hours %"},
    {"headerName": "Days Rig Drilled", "field": "Days Rig Drilled"},
    {"headerName": "Rig Days %", "field": "Rig Days %"},
    {"headerName": "Average Piles/Day", "field": "Average Piles/Day"},
    {"headerName": "AveragePileLength", "field": "AveragePileLength"},

    {
        "headerName": "Delta Piles vs Concrete",
        "field": "Delta_Piles_vs_Concrete",
        "cellStyle": {
            "function": "function(params) {return {color: params.data.DeltaColors['Delta_Piles_vs_Concrete'], textAlign: 'center'};}"
        }
    },
    {
        "headerName": "Delta Piles vs RigDays",
        "field": "Delta_Piles_vs_RigDays",
        "cellStyle": {
            "function": "function(params) {return {color: params.data.DeltaColors['Delta_Piles_vs_RigDays'], textAlign: 'center'};}"
        }
    },
    {
        "headerName": "Delta Piles vs Labor Hours",
        "field": "Delta_Piles_vs_Labor Hours",
        "cellStyle": {
            "function": "function(params) {return {color: params.data.DeltaColors['Delta_Piles_vs_Labor Hours'], textAlign: 'center'};}"
        }
    }
]
date_picker_style = {
    "backgroundColor": "#193153",
    "color": "white",
    "border": "none",
    "borderRadius": "6px",
    "padding": "6px 10px"
}

layout = html.Div([
    # Date picker
    dcc.DatePickerSingle(
        id="date-picker",
        date=date.today(),
        display_format="YYYY-MM-DD",
        style=date_picker_style,
        className="dash-datepicker",
    ),

    # Summary cards
    html.Div(
        id="summary-cards",
        style={"display": "flex", "gap": "20px", "marginTop": "20px"}
    ),

    html.Br(),

    # Job bar chart
    dbc.Row([
        dbc.Col(
            children=[
                dcc.RadioItems(
                    id='metric-toggle',
                    options=[
                        {'label': 'Percentages', 'value': 'percent'},
                        {'label': 'Numbers', 'value': 'actual'}
                    ],
                    value='percent',
                    inline=True,
                    style={
                    'color': 'white',
                    'fontSize': '12px',  # Smaller text
                    'textAlign': 'right',  # Align to right
                    'marginBottom': '10px',
                    'justifyContent': 'flex-end',  # Push to right
                    'display': 'flex',
                    'gap': '15px'  # Space between options
                },
                labelStyle={'marginRight': '10px'}
                ),
                dcc.Graph(
                    id="job-bar-chart",
                    style={
                        "backgroundColor": "#193153",
                        'width': '100%',
                        'height': '500px',
                        'marginBottom': '40px'  # ensures space for labels
                    }
                ),
            ],
            width=12
        )
    ]),

    # Job table
    dbc.Row([
        dbc.Col(
            dag.AgGrid(
                id="job-table",
                columnDefs=column_defs,
                rowData=[],
                defaultColDef={
                    "resizable": True,
                    "sortable": True,
                    "filter": True,
                    "cellStyle": {"textAlign": "center"}
                },
                dashGridOptions={"rowSelection": "single"},
                style={"height": "300px", "width": "100%"},
                className="ag-theme-alpine-dark",
            ),
            width=12
        )
    ], style={"marginTop": "20px"}),

    # Job metrics bar charts
    dbc.Row([
        dbc.Col(
            dcc.Graph(
                id="job-metrics-bar_chart",
                style={
                    "backgroundColor": "#193153",
                    'width': '100%',
                    'height': '800px',
                    'marginTop': '40px',
                    'marginBottom': '40px'
                }

            ),
            width=12
        )
    ]),

    # Job pie chart
    dbc.Row([
        dbc.Col(
            dcc.Graph(
                id="job-pie",
                style={
                    "backgroundColor": "#193153",
                    'width': '100%',
                    'height': '400px',
                    'marginTop': '40px'
                }
            ),
            width=12
        )
    ]),

    # Time chart
    dbc.Row([
        dbc.Col(
            dcc.Graph(
                id="time-chart",
                style={
                    "backgroundColor": "#193153",
                    'width': '100%',
                    'height': '700px',
                    'marginTop': '40px'
                }
            ),
            width=12
        )
    ])
],
style={
    'backgroundColor': '#193153',
    'minHeight': '500vh',  # grow with content
    'padding': '20px'
})
    # style={'backgroundColor': '#193153', 'height': '550vh', 'padding': '20px', 'position': 'relative'})


@callback(
    Output("job-table", "rowData"),
    Output("summary-cards", "children"),
    Input("date-picker", "date"),prevent_initial_call=True
)
def update_table(selected_date):
    selected_date = pd.to_datetime(selected_date)
    table_rows = prepare_table_data(summary_metrics, selected_date)
    table_rows_daily =  prepare_table_data_daily(summary_metrics, selected_date)

    total_piles = table_rows_daily["Piles"]
    total_concrete = table_rows_daily["ConcreteDelivered"]
    total_rig_days = table_rows_daily["DaysRigDrilled"]
    total_labor_hours = table_rows_daily["LaborHours"]

    cards = [
        html.Div(f"# Piles Drilled: {total_piles:.0f}", style={"padding": "10px", "background": "#d4edda", "borderRadius": "8px", "flex": "1"}),
        html.Div(f"Concrete Delivered: {total_concrete:.1f} CY", style={"padding": "10px", "background": "#cce5ff", "borderRadius": "8px", "flex": "1"}),
        html.Div(f"# Man Hours: {total_labor_hours:.0f}", style={"padding": "10px", "background": "#f8d7da", "borderRadius": "8px", "flex": "1"}),
        html.Div(f"# Rig Days: {total_rig_days:.1f}",style={"padding": "10px", "background": "#fff3cd", "borderRadius": "8px", "flex": "1"}),
    ]

    return table_rows, cards

#
@callback(
    Output("job-bar-chart", "figure"),
    Input("date-picker", "date"),
    Input("metric-toggle", "value"),
)
def update_job_bar_chart(selected_date, metric_type):
    # Get filtered data from your summary_metrics
    records = []
    for job, df in summary_metrics.items():
        df_to_date = df[df['Time']<=pd.to_datetime(selected_date)]
        if len(df_to_date)==0:
            raise PreventUpdate
        row = df_to_date.iloc[-1]
        if metric_type == 'percent':
            records.append({
                "JobNumber": job,
                "Piles": round(row["Piles%"] * 100,2),
                "Concrete": round(row["Concrete%"] * 100,2),
                "Rig Days": round(row["RigDays%"] * 100,2),
                "Labor Hours": round(row["LaborHours%"] * 100,2)
            })
        else:
            records.append({
                "JobNumber": job,
                "Piles": row["Piles"] ,
                "Concrete": row["ConcreteDelivered"],
                "Rig Days": row["DaysRigDrilled"],
                "Labor Hours": row["LaborHours"]
            })

    if not records:
        return px.bar(title="No data available for selected date")

    df_chart = pd.DataFrame(records)

    #  Melt dataframe so Plotly can group bars
    df_melted = df_chart.melt(id_vars="JobNumber",
                              value_vars=["Piles", "Concrete", "Rig Days", "Labor Hours"],
                              var_name="Metric",
                              value_name="Value")

    fig = px.bar(
        df_melted,
        x="JobNumber",
        y="Value",
        color="Metric",
        barmode="group",
        text="Value",
        title=f"Job Performance Metrics at {selected_date}"
    )

    # Update axis labels based on metric type
    if metric_type == 'percent':
        yaxis_title = "Percent (%)"
        text_template = "%{text:.1f}%"
    else:
        yaxis_title = "Actual Values"
        text_template = "%{text:.0f}"

    fig.update_traces(texttemplate=text_template)

    fig.update_layout(
        yaxis_title=yaxis_title,
        xaxis_title="Job Number",
        legend_title="Metric",
        template="plotly_white"
    )

    fig.update_xaxes(type='category')

    fig.update_layout(
        plot_bgcolor="#193153",
        paper_bgcolor="#193153",
        font=dict(color="white"),
        showlegend=True,
        dragmode="select",
        margin=dict(l=40, r=40, t=40, b=100),
        autosize=False,
        height=500
    )

    return fig


@callback(
    Output("job-pie", "figure"),
    Input("job-table", "selectedRows"),
    Input("date-picker", "date")#,prevent_initial_call=True
)

def update_pie(selected_rows,selected_date):
    if not selected_rows:
        # return px.pie(title="Select a row to see details")
        return go.Figure(layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"})

    row = selected_rows[0]

    # # Get the selected row's data
    df_daily = prepare_time_spent_stats(summary_dic_daily)
    # # Filter by JobID and date
    df = df_daily[
        (df_daily['JobID'] == row['JobNumber']) &
        (pd.to_datetime(df_daily['Time']).dt.date == pd.to_datetime(selected_date).date())
        ]

    if df.empty:
        return go.Figure(layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"})

    # Get unique RigIDs
    rig_ids = df['RigID'].unique()
    num_rigs = len(rig_ids)

    # Create subplot layout for pies
    fig = make_subplots(
        rows=1,
        cols=num_rigs,
        specs=[[{'type': 'domain'}] * num_rigs],
        subplot_titles=[f"Rig {rig}" for rig in rig_ids]
    )

    # Add one pie per RigID
    for i, rig in enumerate(rig_ids, start=1):
        rig_data = df[df['RigID'] == rig]
        piles = str(rig_data['Piles'].values[0])
        values = [
            rig_data['MoveTime'].sum(),
            rig_data['DrillTime'].sum(),
            rig_data['GroutTime'].sum(),
            rig_data['InstallTime'].sum(),
            rig_data['DelayTime'].sum(),
        ]
        labels = ["Avg MoveTime", "Avg DrillTime", "Avg GroutTime", "Avg InstallTime", "Avg DelayTime"]

        fig.add_trace(
            go.Pie(labels=labels, values=values, name=f"Rig {rig}"),
            row=1, col=i
        )

        fig.layout.annotations[i - 1].text = f"Rig {rig} — Piles: {piles}"

    fig.update_layout(title_text=f"Job {row['JobNumber']} Breakdown by Rig on {selected_date}")
    fig.update_layout(
        plot_bgcolor="#193153",
        paper_bgcolor="#193153",
        font=dict(color="white"),
        showlegend=True,
        dragmode="select",
        autosize=False,
        height=400
        # margin=dict(l=50, r=50, b=50, t=50, pad=4)
    )

    return fig

@callback(
    Output("time-chart", "figure"),
    Input("job-table", "selectedRows"),
    Input("date-picker", "date"),
    # prevent_initial_call=True
)
def update_time_chart(selected_rows, selected_date):
    if not selected_rows:
        return go.Figure(layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"})

    row = selected_rows[0]
    job = row['JobNumber']

    # Fast check using cache manager
    if not cache_manager.is_date_available(job, selected_date):
        return go.Figure(layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"})

    # GET PRECOMPUTED DATA - This is now instant!
    precomputed_data = cache_manager.get_precomputed_rig_data(job, selected_date)

    if not precomputed_data or not precomputed_data['rig_pile_dataframes']:
        raise PreventUpdate

    piles_by_rig = precomputed_data['piles_by_rig']
    rig_pile_dataframes = precomputed_data['rig_pile_dataframes']

    # Create subplots with secondary y-axis
    fig = make_subplots(
        rows=len(piles_by_rig),
        cols=1,
        shared_xaxes=True,
        subplot_titles=[f"Rig {r}" for r in piles_by_rig.keys()],
        vertical_spacing=0.12,
        specs=[[{"secondary_y": True}]] * len(piles_by_rig)
    )

    # Consistent colors
    DEPTH_COLOR = '#1E90FF'    # Bright blue
    STROKES_COLOR = '#006400'  # Dark green
    TORQUE_COLOR = '#FFD700'   # Gold/yellow

    annotations = []

    # Loop rigs
    for i, (rig_id, pile_ids) in enumerate(piles_by_rig.items(), start=1):
        if rig_id not in rig_pile_dataframes:
            continue

        pile_data_dict = rig_pile_dataframes[rig_id]

        for pile_idx, (pile_id, pile_df) in enumerate(pile_data_dict.items()):
            # Depth trace
            fig.add_trace(
                go.Scatter(
                    x=pile_df['Time'],
                    y=-pile_df['Depth'],
                    mode='lines',
                    name='Depth',
                    line=dict(color=DEPTH_COLOR, width=2),
                    hoverinfo='text +y',
                    # hovertext=f'Pile {pile_id}: Depth',
                    hovertext='Depth',
                    # hovertemplate='Time: %{x}<br>Depth: %{y}<extra></extra>',
                    legendgroup='Depth',
                    showlegend=(i == 1 and pile_idx == 0),
                    opacity=0.8
                ),
                row=i, col=1, secondary_y=False
            )

            # Strokes trace
            fig.add_trace(
                go.Scatter(
                    x=pile_df['Time'],
                    y=pile_df['Strokes'],
                    mode='lines',
                    name='Strokes',
                    line=dict(color=STROKES_COLOR, width=2),
                    # hovertemplate='Time: %{x}<br>Strokes: %{y}<extra></extra>',
                    hoverinfo='x+y+text',
                    hovertext='Strokes',
                    # hovertext=f'Pile {pile_id}: Strokes',
                    legendgroup='Strokes',
                    showlegend=(i == 1 and pile_idx == 0),
                    opacity=0.8
                ),
                row=i, col=1, secondary_y=False
            )

            # Torque trace
            fig.add_trace(
                go.Scatter(
                    x=pile_df['Time'],
                    y=pile_df['Torque'],
                    mode='lines',
                    name='Torque',
                    line=dict(color=TORQUE_COLOR, width=2),
                    hoverinfo='x+y+text',
                    # hovertext=f'Pile {pile_id}: Torque',
                    hovertext='Torque',
                    # hovertemplate='Time: %{x}<br>Torque: %{y}<extra></extra>',
                    legendgroup='Torque',
                    showlegend=(i == 1 and pile_idx == 0),
                    opacity=0.8
                ),
                row=i, col=1, secondary_y=True
            )

            # Add annotation for this pile
            if not pile_df.empty:
                mid_idx = len(pile_df) // 2
                annotation_time = pile_df['Time'].iloc[mid_idx]
                # Staggered offset to avoid overlapping labels
                annotation_depth = -pile_df['Depth'].min() * 0.95 + (pile_idx * 0.5)

                # correct axis refs (primary y-axis for subplot i)
                xref = "x" if i == 1 else f"x{i}"
                yref = "y" if i == 1 else f"y{2*i-1}"

                annotations.append(dict(
                    x=annotation_time,
                    y=annotation_depth,
                    xref=xref,
                    yref=yref,
                    text=f"P{pile_id}",
                    showarrow=False,
                    font=dict(size=10, color="white"),
                    bgcolor="rgba(0,0,0,0.5)",
                    bordercolor="rgba(255, 255, 255, 0.3)",
                    borderwidth=1,
                    borderpad=2,
                    opacity=0.8
                ))


    # Layout
    fig.update_layout(
        height=350 * len(piles_by_rig),
        plot_bgcolor="#193153",
        paper_bgcolor="#193153",
        font_color="white",
        showlegend=True,
        margin=dict(l=50, r=80, t=50, b=50),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.1,
            font=dict(size=11),
            bgcolor='rgba(25, 49, 83, 0.9)',
            bordercolor='rgba(255, 255, 255, 0.3)',
            borderwidth=1
        ),
        annotations=annotations
    )

    # Axes config
    for i in range(1, len(piles_by_rig) + 1):
        fig.update_yaxes(
            title_text="Depth/Strokes",
            row=i, col=1,
            secondary_y=False,
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.1)',
            zeroline=False
        )
        fig.update_yaxes(
            title_text="Torque",
            row=i, col=1,
            secondary_y=True,
            showgrid=False,
            zeroline=False
        )
        #
        fig.update_xaxes(
            title_text="Time" if i == len(piles_by_rig) else None,  # keep title only on bottom
            row=i, col=1,
            showgrid=True,
            showticklabels=True,  # 👈 force tick labels for *all* subplots
            gridcolor='rgba(255, 255, 255, 0.1)',
            title_standoff=5
        )
        fig.update_xaxes(showspikes=False)
        fig.update_yaxes(showspikes=False)

    return fig




@callback(Output('job-metrics-bar_chart', 'figure'),
          Input("job-table", "selectedRows"),
          Input("date-picker", "date"),
          # prevent_initial_call=True
          )
def update_time_chart(selected_rows, selected_date):
    if not selected_rows:
        return go.Figure(layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"})

    row = selected_rows[0]
    job = row['JobNumber']
    data = summary_metrics[job]

    # Create subplots with secondary y-axes
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("Piles & Concrete Delivered", "Labor Hours & Rig Days"),
        specs=[[{"secondary_y": True}], [{"secondary_y": True}]]
    )

    # Consistent colors for all measurements
    BLUE_COLOR = '#1E90FF'  # Bright blue
    GREEN_COLOR = '#006400'  # Dark green
    YELLOW_COLOR = '#FFD700'  # Gold/yellow
    RED_COLOR = '#FF4500'  # Orange-red (for secondary axes)

    # First row: Piles (primary) and ConcreteDelivered (secondary)
    fig.add_trace(
        go.Bar(
            x=data['Time'],
            y=data['Piles'],
            name='Piles',
            marker_color=BLUE_COLOR,
            opacity=0.7,
            offsetgroup="1",
        ),
        row=1, col=1,
        secondary_y=False
    )

    fig.add_trace(
        go.Bar(
            x=data['Time'],
            y=data['ConcreteDelivered'],
            name='Concrete Delivered',
            marker_color=YELLOW_COLOR,
            opacity=0.7,
            offsetgroup="2",
        ),
        row=1, col=1,
        secondary_y=True
    )

    # Second row: LaborHours (primary) and RigDays (secondary)
    fig.add_trace(
        go.Bar(
            x=data['Time'],
            y=data['LaborHours'],
            name='Labor Hours',
            marker_color=GREEN_COLOR,
            opacity=0.7,
            offsetgroup="1",
        ),
        row=2, col=1,
        secondary_y=False
    )

    fig.add_trace(
        go.Bar(
            x=data['Time'],
            y=data['DaysRigDrilled'],
            name='Rig Days',
            marker_color=RED_COLOR,
            opacity=0.7,
            offsetgroup="2",
        ),
        row=2, col=1,
        secondary_y=True
    )

    # Update layout
    fig.update_layout(
        height=800,
        autosize=False,
        plot_bgcolor="#193153",
        paper_bgcolor="#193153",
        font_color="white",
        showlegend=True,
        # margin=dict(l=50, r=80, t=80, b=50),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.01,
            font=dict(size=11),
            bgcolor='rgba(25, 49, 83, 0.9)',
            # bordercolor='rgba(255, 255, 255, 0.3)',
            # borderwidth=1
        ),
        barmode='group'
    )

    # Update y-axis titles and colors
    # First row axes
    fig.update_yaxes(title_text="Piles", row=1, col=1, secondary_y=False, showgrid=True, gridcolor="grey")
    fig.update_yaxes(title_text="Concrete Delivered", row=1, col=1, secondary_y=True, showgrid=False)


    # Second row axes
    fig.update_yaxes(title_text="Labor Hours", row=2, col=1, secondary_y=False, showgrid=True, gridcolor="grey")
    fig.update_yaxes(title_text="Rig Days", row=2, col=1, secondary_y=True, showgrid=False)


    # Update x-axis title for the bottom subplot
    fig.update_xaxes(title_text="Time", row=2, col=1)

    # Update subplot title styles
    fig.update_annotations(font_color="white", font_size=14)


    return fig


# add bar chart showing pile/concrete/labour hours and pile length /rig days every day.