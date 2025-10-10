
from dash import dcc, html, Output, Input, State, callback,no_update,ctx, MATCH, ALL
import plotly.express as px
from dash.exceptions import PreventUpdate
import pandas as pd
import os
import dash
import dash_ag_grid as dag
from datetime import date,timedelta
from collections import defaultdict
import holidays
import dash_bootstrap_components as dbc
from data_loader import ensure_data_loaded

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from layouts import add_drilling_summary


dash.register_page(
    __name__,
    path_template="/Metrics",
    path="/Metrics",
)

assets_path = os.path.join(os.getcwd(), "assets")
summary_folder = os.path.join(assets_path, 'data','Summary')

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


def calculate_expected_progress_with_holidays(start_date, total_piles, piles_per_day):
    dates = []
    expected_piles = []
    current_date = start_date
    cumulative_piles = 0

    # Ensure start date is a working day
    while not is_working_day(current_date):
        current_date = next_working_day(current_date)

    while cumulative_piles < total_piles:
        dates.append(current_date)
        cumulative_piles = min(cumulative_piles + piles_per_day, total_piles)
        expected_piles.append(cumulative_piles)

        current_date = next_working_day(current_date)

    return pd.DataFrame({
        'Date': dates,
        'Expected': expected_piles
    })
# Get data from cache
def get_data_summary(value:str):
    data = ensure_data_loaded()
    return data[value]

def count_piles_for_date(data, target_date):
    return sum(1 for pile_data in data.values() if target_date in pile_data)


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

def load_data_metrics():
    # summary_dict_to_date = {}
    summary_dict_daily = {}
    summary_metrics ={}

    my_jobs = get_data_summary('my_jobs')
    df_stats = pd.DataFrame()
    for jb,job in my_jobs.jobs.items():
         summary_metrics[jb] = job.job2data_stats
         summary_dict_daily[jb] = job.daily_stats
         tmp = job.job2data_stats_complete
         tmp['JobNo'] = job.job_id
         tmp['JobName'] = job.job_name
         df_stats = pd.concat([df_stats,tmp],ignore_index=True)

    return summary_metrics,summary_dict_daily,df_stats


# ======================
# Prepare AG Grid data
# ======================
def prepare_table_data(summary_metrics, selected_date):
    rows = []
    my_jobs = get_data_summary('my_jobs')
    for job, df in summary_metrics.items():
        if len(df)==0:
            continue
        df_on_date = df[pd.to_datetime(df['Time']) <= selected_date].sort_values('Time')
        if len(df_on_date) < 2:
            continue

        current = df_on_date.iloc[-1]

        # previous = df_on_date.iloc[-2]

        # def format_delta(curr, prev):
        #     if pd.isna(curr):
        #         return "", "black"
        #     if pd.isna(prev) or curr == prev:
        #         return f"→ {curr:.1f}%", "black"
        #     elif curr > prev:
        #         return f"↑ {curr:.1f}%", "red"  # worse
        #     else:
        #         return f"↓ {curr:.1f}%", "green"  # better

        # delta_cells = {}
        # delta_colors = {}
        # for col in ['Delta_Piles_vs_Concrete', 'Delta_Piles_vs_RigDays', 'Delta_Piles_vs_Labor Hours']:
        #     text, color = format_delta(current[col]*100, previous[col]*100)
        #     delta_cells[col] = text
        #     delta_colors[col] = color

        # Status classification
        # max_delta = max(abs(current['Delta_Piles_vs_Concrete']),
        #                 abs(current['Delta_Piles_vs_RigDays']),
        #                 abs(current['Delta_Piles_vs_Labor Hours']))
        # max_delta=abs(max_delta*100)
        # if max_delta < 5:
        #     status = "green"
        #     status_symbol = "✅"
        # elif max_delta <= 10:
        #     status = "orange"
        #     status_symbol = "⚠"
        # else:
        #     status = "red"
        #     status_symbol = "❌"
        piles_per_day = round(current['Piles']/current['DaysRigDrilled'],0)
        rows.append({
            "JobID": str(job) +'-'+ str(my_jobs.jobs[job].job_name),
            "JobNumber": str(job),
            # "StatusSymbol": status_symbol,
            # "StatusColor": status,
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
            # "Delta_Piles_vs_Concrete": delta_cells['Delta_Piles_vs_Concrete'],
            # "Delta_Piles_vs_RigDays": delta_cells['Delta_Piles_vs_RigDays'],
            # "Delta_Piles_vs_Labor Hours": delta_cells['Delta_Piles_vs_Labor Hours'],
            # "DeltaColors": delta_colors
        })

    return rows




def prepare_table_data_daily(summary_metrics, selected_date):
    rows = []
    total_piles = 0
    total_concrete = 0
    total_rig_days = 0
    total_labor_hours = 0

    for job, df in summary_metrics.items():
        if len(df)==0:
            continue
        df['Piles_delta'] = df['Piles'].diff()
        df['Concrete_delta'] = df['ConcreteDelivered'].diff()
        df['DaysRig_delta'] = df['DaysRigDrilled'].diff()
        df['ManHours_delta'] = df['LaborHours'].diff()
        df_on_date = df[pd.to_datetime(df['Time']) == pd.to_datetime(selected_date)].sort_values('Time')
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

def prepare_time_spent_stats(summary_dict_daily,jobID):

    out_df = pd.DataFrame()
    df = summary_dict_daily[jobID]
    # for job, df in summary_dict_daily.items():
    tmp = df[['Time','RigID','Piles']]
    tmp['JobID'] = jobID
    for name in df.columns:
        if name.startswith('mean_') and name.endswith('Time'):
            name_= name.split('_')[1]
            tmp[name_] = df[name].str.split('min',expand=True)[0]
            # tmp[name_] = pd.to_datetime(tmp[name_],format = '%H:%M:%S')
            # tmp[name_] = pd.to_numeric(tmp[name_],errors= 'coerce')

    out_df = pd.concat([out_df,tmp],ignore_index=True)

    return out_df


summary_metrics,summary_dic_daily,df_stats = load_data_metrics()

# ======================
# Dash AG Grid
# ======================
column_defs = [
    {"headerName": "JobID", "field": "JobID","cellStyle": {"textAlign": "left"}},
    {"headerName": "JobNumber", "field": "JobNumber","hide": True},
    # {
    #     "headerName": "Status",
    #     "field": "StatusSymbol",
    #     "cellStyle": {
    #         "function": """
    #             function(params) {
    #                 if (params.data.StatusColor === 'green') return {backgroundColor: '#d4edda', textAlign: 'center'};
    #                 if (params.data.StatusColor === 'orange') return {backgroundColor: '#fff3cd', textAlign: 'center'};
    #                 if (params.data.StatusColor === 'red') return {backgroundColor: '#f8d7da', textAlign: 'center'};
    #                 return {textAlign: 'center'};
    #             }
    #         """
    #     }
    # },
    {"headerName": "Piles Drilled", "field": "Piles Drilled"},
    {"headerName": "Piles %", "field": "Piles %"},
    {"headerName": "Concrete Delivered (cyd)", "field": "Concrete Delivered"},
    {"headerName": "Concrete %", "field": "Concrete %"},
    {"headerName": "Labor Hours", "field": "Labor Hours"},
    {"headerName": "Labor Hours %", "field": "Labor Hours %"},
    {"headerName": "Days Rig Drilled", "field": "Days Rig Drilled"},
    {"headerName": "Rig Days %", "field": "Rig Days %"},
    {"headerName": "Average Piles/Day", "field": "Average Piles/Day"},
    {"headerName": "Average PileLength (ft)", "field": "AveragePileLength"},

    # {
    #     "headerName": "Delta Piles vs Concrete",
    #     "field": "Delta_Piles_vs_Concrete",
    #     "cellStyle": {
    #         "function": "function(params) {return {color: params.data.DeltaColors['Delta_Piles_vs_Concrete'], textAlign: 'center'};}"
    #     }
    # },
    # {
    #     "headerName": "Delta Piles vs RigDays",
    #     "field": "Delta_Piles_vs_RigDays",
    #     "cellStyle": {
    #         "function": "function(params) {return {color: params.data.DeltaColors['Delta_Piles_vs_RigDays'], textAlign: 'center'};}"
    #     }
    # },
    # {
    #     "headerName": "Delta Piles vs Labor Hours",
    #     "field": "Delta_Piles_vs_Labor Hours",
    #     "cellStyle": {
    #         "function": "function(params) {return {color: params.data.DeltaColors['Delta_Piles_vs_Labor Hours'], textAlign: 'center'};}"
    #     }
    # }
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
        date=date.today() - timedelta(days=1),
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
                        'fontSize': '12px',
                        'textAlign': 'right',
                        'marginBottom': '10px',
                        'justifyContent': 'flex-end',
                        'display': 'flex',
                        'gap': '15px'
                    },
                    labelStyle={'marginRight': '10px'}
                ),
                dcc.Graph(
                    id="job-bar-chart",
                    style={
                        "backgroundColor": "#193153",
                        'width': '100%',
                        'height': '500px',
                        'marginBottom': '40px'
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
    html.Br(),
    add_drilling_summary(),

    dbc.Button("Show Job Metrics Bar Charts", id="toggle-bar-chart", color="primary", className="mb-2", style={"marginTop": "20px"}),

    # Job metrics bar charts
    dbc.Collapse(
        html.Div([
        dbc.Row([
            dbc.Col(
                children=[
                    dcc.RadioItems(
                        id='metric-toggle-daily',
                        options=[
                            {'label': 'Cumulative', 'value': 'cumulative'},
                            {'label': 'Daily', 'value': 'daily'}
                        ],
                        value='daily',
                        inline=True,
                        style={
                            'color': 'white',
                            'fontSize': '12px',
                            'textAlign': 'right',
                            'marginTop': '20px',
                            'justifyContent': 'flex-end',
                            'display': 'flex',
                            'gap': '15px'
                        },
                        labelStyle={'marginRight': '10px'}
                    ),
                    dcc.Graph(
                        id="job-metrics-bar_chart",
                        style={
                            "backgroundColor": "#193153",
                            'width': '100%',
                            'height': '800px',
                            'marginTop': '10px',
                            'marginBottom': '40px'
                        }
                    )],
                width=12
            )
        ]),
        ]),#close html.Div
        id="collapse-job-metrics-bar_chart",
        is_open=False
    ),

    # job-metrics-line_chart
    dbc.Button("Show Job Metrics Line Charts", id="toggle-line-chart", color="primary", className="mb-2", style={"marginTop": "20px"}),

    dbc.Collapse(
        html.Div([
            dbc.Row([
                dbc.Col(
                    children=[
                        dcc.Graph(
                            id="job-metrics-line_chart",
                            style={
                                "backgroundColor": "#193153",
                                'width': '100%',
                                'height': '800px',
                                'marginTop': '10px',
                                'marginBottom': '40px'
                            }
                        )],
                    width=12
                )
            ]),
        ]),  #close DIV
        id="collapse-job-metrics-line_chart",
        is_open=False
        ),#clode collapse

    # Job pie chart
    dbc.Button("Show Job Metrics Pie Charts", id="toggle-pie-chart", color="primary", className="mb-2", style={"marginTop": "20px"}),

    dbc.Collapse(
        html.Div([
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
            ]),#close DIV
        id="collapse-job-metrics-pie_chart",
        is_open=False
    ),#close collapse
    html.Hr(),
    html.Div(id="rig-charts-container"),
],
    style={
        'backgroundColor': '#193153',
        'minHeight': '500vh',
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
    table_rows_daily = prepare_table_data_daily(summary_metrics, selected_date)

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
        if len(df)==0:
            continue
        try:
            df_to_date = df[pd.to_datetime(df['Time'])<=pd.to_datetime(selected_date)]
        except:
            raise PreventUpdate
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


from datetime import timedelta


def sum_timestamps(time_strings):
    total_seconds = 0
    for time_str in time_strings:
        if str(time_str)!='nan':
            h, m, s = map(int, time_str.split(':'))
            total_seconds += h * 3600 + m * 60 + s

    # Convert back to time format
    # total_time = timedelta(seconds=total_seconds)

    return total_seconds/60 # returns minutes
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
    df_daily = prepare_time_spent_stats(summary_dic_daily,row['JobNumber'])
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
            sum_timestamps(rig_data['MoveTime']),
            sum_timestamps(rig_data['DrillTime']),
            sum_timestamps(rig_data['GroutTime']),
            sum_timestamps(rig_data['InstallTime']),
            sum_timestamps(rig_data['DelayTime']),
            # rig_data['MoveTime'].sum(),
            # rig_data['DrillTime'].sum(),
            # rig_data['GroutTime'].sum(),
            # rig_data['InstallTime'].sum(),
            # rig_data['DelayTime'].sum(),
        ]
        labels = ["Avg MoveTime", "Avg DrillTime", "Avg GroutTime", "Avg InstallTime", "Avg DelayTime"]

        fig.add_trace(
            go.Pie(labels=labels, values=values, name=f"Rig {rig}"),
            row=1, col=i
        )

        fig.layout.annotations[i - 1].text = f"Rig {rig} — Piles: {piles}"

    fig.update_layout(title_text=f"Job {row['JobID']} Breakdown by Rig on {selected_date}")
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


@callback(Output('job-metrics-bar_chart', 'figure'),
          Input("job-table", "selectedRows"),
          Input("date-picker", "date"),
          Input("metric-toggle-daily", "value")
          # prevent_initial_call=True
          )
def update_time_chart(selected_rows, selected_date,metric_unit):
    if not selected_rows:
        return go.Figure(layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"})

    row = selected_rows[0]
    job = row['JobNumber']
    data = summary_metrics[job]
    if metric_unit == 'cumulative':
        subplot_titles = ("Piles & Concrete (cumulative)", "Labor Hours & Rig Days (cumulative)")
    else:
        subplot_titles = ("Piles & Concrete (daily)", "Labor Hours & Rig Days (daily)")
    # Create subplots with secondary y-axes
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=subplot_titles,
        specs=[[{"secondary_y": True}], [{"secondary_y": True}]]
    )

    # Consistent colors for all measurements
    BLUE_COLOR = '#1E90FF'  # Bright blue
    GREEN_COLOR = '#006400'  # Dark green
    YELLOW_COLOR = '#FFD700'  # Gold/yellow
    RED_COLOR = '#FF4500'  # Orange-red (for secondary axes)

    if metric_unit=='cumulative':
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
                name='Concrete',
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
    else:
        # First row: Piles (primary) and ConcreteDelivered (secondary)
        fig.add_trace(
            go.Bar(
                x=data['Time'],
                y=data['Piles'].diff(),
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
                y=data['ConcreteDelivered'].diff(),
                name='Concrete',
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
                y=data['LaborHours'].diff(),
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
                y=data['DaysRigDrilled'].diff(),
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
@callback(Output('job-metrics-line_chart', 'figure'),
          Input("job-table", "selectedRows"),
          Input("date-picker", "date"),
          # Input("metric-toggle-daily", "value")
          # prevent_initial_call=True
          )
def update_line_chart(selected_rows, selected_date):
    if not selected_rows:
        return go.Figure(layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"})

    row = selected_rows[0]
    job = row['JobNumber']
    data = summary_metrics[job]
    my_jobs = get_data_summary('my_jobs')
    df_expected = my_jobs.jobs[job].df_expected
    data = data[pd.to_datetime(data['Time'])>=my_jobs.jobs[job].start_date]
    subplot_titles =''
    # Create subplots with secondary y-axes
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=subplot_titles,
        # specs=[[{"secondary_y": True}], [{"secondary_y": True}]]
    )

    # Consistent colors for all measurements
    BLUE_COLOR = '#1E90FF'  # Bright blue
    GREEN_COLOR = '#006400'  # Dark green

    # First row: Piles (primary)
    fig.add_trace(
        go.Scatter(
            x=data['Time'],
            y=data['Piles'],
            name='Actual',  # Changed to generic 'Actual'
            mode='lines+markers',
            line=dict(color=BLUE_COLOR, width=2),
            showlegend=True  # Show legend for first Actual trace
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_expected['date'],
            y=df_expected['expected_piles'],
            name='Estimate',  # Changed to generic 'Estimate'
            mode='lines+markers',
            line=dict(color=GREEN_COLOR, width=2),
            showlegend=True  # Show legend for first Estimate trace
        ),
        row=1, col=1,
    )
    # ConcreteDelivered
    fig.add_trace(
        go.Scatter(
            x=data['Time'],
            y=data['ConcreteDelivered'],
            name='Actual',  # Same name as first Actual
            mode='lines+markers',
            line=dict(color=BLUE_COLOR, width=2),
            showlegend=False  # Don't show in legend (already shown)
        ),
        row=2, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_expected['date'],
            y=df_expected['expected_concrete'],
            name='Estimate',  # Same name as first Estimate
            mode='lines+markers',
            line=dict(color=GREEN_COLOR, width=2),
            showlegend=False  # Don't show in legend (already shown)
        ),
        row=2, col=1,
    )

    # Third row: LaborHours (primary)
    fig.add_trace(
        go.Scatter(
            x=data['Time'],
            y=data['LaborHours'],
            name='Actual',  # Same name as first Actual
            mode='lines+markers',
            line=dict(color=BLUE_COLOR, width=2),
            showlegend=False  # Don't show in legend (already shown)
        ),
        row=3, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_expected['date'],
            y=df_expected['expected_labour'],
            name='Estimate',  # Same name as first Estimate
            mode='lines+markers',
            line=dict(color=GREEN_COLOR, width=2),
            showlegend=False  # Don't show in legend (already shown)
        ),
        row=3, col=1,
    )

    # Update layout
    fig.update_layout(
        height=800,
        autosize=False,
        plot_bgcolor="#193153",
        paper_bgcolor="#193153",
        font_color="white",
        showlegend=True,
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="right",
            x=1.02,
            font=dict(size=11),
            bgcolor='rgba(25, 49, 83, 0.9)',
        ),
        barmode='group'
    )

    # Update y-axis titles and colors with grey grid lines and axis lines
    # Update y-axes
    fig.update_yaxes(
        title_text="Piles",
        row=1, col=1,
        showgrid=True,
        gridcolor="grey",
        gridwidth=1,
        linecolor="grey",
        linewidth=1,
        showline=True,
        mirror=True,
        zeroline=True,  # Add this
        zerolinecolor="grey",  # Add this
        zerolinewidth=1  # Add this
    )
    fig.update_yaxes(
        title_text="Concrete Delivered",
        row=2, col=1,
        showgrid=True,
        gridcolor="grey",
        gridwidth=1,
        linecolor="grey",
        linewidth=1,
        showline=True,
        mirror=True,
        zeroline=True,  # Add this
        zerolinecolor="grey",  # Add this
        zerolinewidth=1  # Add this
    )
    fig.update_yaxes(
        title_text="Labor Hours",
        row=3, col=1,
        showgrid=True,
        gridcolor="grey",
        gridwidth=1,
        linecolor="grey",
        linewidth=1,
        showline=True,
        mirror=True,
        zeroline=True,  # Add this
        zerolinecolor="grey",  # Add this
        zerolinewidth=1  # Add this
    )

    # For the first subplot
    fig.update_xaxes(
        row=1, col=1,
        showgrid=True,
        gridcolor="grey",
        gridwidth=1,
        showline=False,
        linecolor="grey",
        linewidth=1,
        zeroline=True,  # Add this
        zerolinecolor="grey",  # Add this
        zerolinewidth=1  # Add this
    )

    # For the second subplot
    fig.update_xaxes(
        row=2, col=1,
        showgrid=True,
        gridcolor="grey",
        gridwidth=1,
        showline=False,
        linecolor="grey",
        linewidth=1,
        zeroline=True,  # Add this
        zerolinecolor="grey",  # Add this
        zerolinewidth=1  # Add this
    )

    # For the third subplot
    fig.update_xaxes(
        title_text="Date",
        row=3, col=1,
        showgrid=True,
        gridcolor="grey",
        gridwidth=1,
        showline=True,
        linecolor="grey",
        linewidth=1,
        zeroline=True,  # Add this
        zerolinecolor="grey",  # Add this
        zerolinewidth=0.5  # Add this
    )

    # Update subplot title styles
    fig.update_annotations(font_color="white", font_size=14)

    return fig


@callback(
    Output("collapse-job-metrics-bar_chart", "is_open"),
    [Input("toggle-bar-chart", "n_clicks")],
    [State("collapse-job-metrics-bar_chart", "is_open")],prevent_initial_call=True
)
def toggle_views(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@callback(
    Output("collapse-job-metrics-line_chart", "is_open"),
    [Input("toggle-line-chart", "n_clicks")],
    [State("collapse-job-metrics-line_chart", "is_open")],prevent_initial_call=True
)
def toggle_views(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

@callback(
    Output("collapse-job-metrics-pie_chart", "is_open"),
    [Input("toggle-pie-chart", "n_clicks")],
    [State("collapse-job-metrics-pie_chart", "is_open")],prevent_initial_call=True
)
def toggle_views(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open





# =======================================

@callback(
    Output("rig-charts-container", "children"),
    [Input("job-table", "selectedRows"),
     Input("date-picker", "date"),
     Input({"type": "pile-location-chart", "rig_id": ALL}, "clickData")],
    [State("rig-charts-container", "children")]
)
def update_rig_charts(selected_rows, selected_date, click_data_list, current_children):
    # Determine what triggered the callback
    triggered_id = ctx.triggered[0]['prop_id'] if ctx.triggered else None

    # Handle initial load or no selection
    if not selected_rows and not triggered_id:
        return []

    # If triggered by click but no selected rows, use current children
    if not selected_rows and triggered_id and triggered_id != 'job-table.selectedRows':
        return current_children or []

    row = selected_rows[0] if selected_rows else None
    if row:
        job = row['JobNumber']
    else:
        # Try to get job from existing charts or return current children
        return current_children or []

    # Fast check using cache manager
    cache_manager = get_data_summary('cache_manager')
    if not cache_manager.is_date_available(job, selected_date):
        return []

    # GET PRECOMPUTED DATA
    precomputed_data = cache_manager.get_precomputed_rig_data(job, selected_date)

    if not precomputed_data or not precomputed_data['rig_pile_dataframes']:
        raise PreventUpdate

    piles_by_rig = precomputed_data['piles_by_rig']
    rig_pile_dataframes = precomputed_data['rig_pile_dataframes']
    result_MWD = get_data_summary('result_MWD')
    df_prop = result_MWD[str(job)][0]

    # Get selected pile from click (if any)
    selected_pile_id = None
    if triggered_id and 'pile-location-chart' in triggered_id and click_data_list:
        # Find the actual click data that triggered the callback
        for click_data in click_data_list:
            if click_data and 'points' in click_data and click_data['points']:
                selected_pile_id = click_data['points'][0]['customdata'][0]
                break

    # Create chart pairs for each rig
    chart_components = []
    rigs =list(piles_by_rig.keys())
    rigs = [x for x in rigs if not x is None]
    for index, rig_id in enumerate(rigs):
        if rig_id not in rig_pile_dataframes:
            continue

        # Create location chart for this rig
        location_fig = create_rig_location_chart(index,rig_id, piles_by_rig[rig_id], rig_pile_dataframes[rig_id], df_prop,
                                                 selected_pile_id)

        # Create time chart for this rig
        time_fig = create_rig_time_chart(rig_id, piles_by_rig[rig_id], rig_pile_dataframes[rig_id], selected_pile_id)

        # Add charts to components with pattern matching IDs
        chart_components.extend([
            html.H3(f"Rig {rig_id}", style={'color': 'white', 'marginTop': '20px', 'marginBottom': '10px'}),
            dcc.Graph(
                id={"type": "pile-location-chart", "rig_id": rig_id},
                figure=location_fig,
                config={'displayModeBar': True,'displaylogo': False},
                style={'height': '400px'}
            ),
            dcc.Graph(
                id={"type": "time-chart", "rig_id": rig_id},
                figure=time_fig,
                config={'displayModeBar': True,'displaylogo': False},
                style={'height': '400px'}
            ),
            html.Hr(style={'borderColor': 'rgba(255,255,255,0.2)', 'margin': '20px 0'})
        ])

    return chart_components


def create_rig_time_chart(rig_id, pile_ids, pile_data_dict, selected_pile_id=None):
    """Create time chart for a specific rig"""
    # Create subplot for this rig only
    fig = make_subplots(
        specs=[[{"secondary_y": True}]],
        subplot_titles=[f"Rig {rig_id} - Time Data"]
    )

    # Consistent colors
    DEPTH_COLOR = '#1E90FF'  # Bright blue
    STROKES_COLOR = 'green'  # Dark green
    TORQUE_COLOR = '#FFD700'  # Gold/yellow
    HIGHLIGHT_COLOR = '#FF1493'  # Bright pink for highlighting

    annotations = []

    for pile_idx, mdict in enumerate(pile_data_dict):
        pile_id = list(mdict.keys())[0]
        pile_df = mdict[pile_id]

        # Determine if this pile should be highlighted
        is_highlighted = (selected_pile_id == pile_id)
        line_width = 4 if is_highlighted else 2
        # line_color = HIGHLIGHT_COLOR if is_highlighted else DEPTH_COLOR
        depth_color = DEPTH_COLOR
        # Depth trace
        fig.add_trace(
            go.Scatter(
                x=pile_df['Time'],
                y=-pile_df['Depth'],
                mode='lines',
                name='Depth',
                line=dict(color=depth_color, width=line_width),
                hoverinfo='text +y',
                hovertext=f'Depth', #Pile {pile_id}:
                legendgroup='Depth',
                showlegend=(pile_idx == 0),
                opacity=0.8 if not is_highlighted else 1.0,
                customdata=[pile_id] * len(pile_df)
            ),
            secondary_y=False
        )

        # Strokes trace (with appropriate color for highlighting)
        # strokes_color = HIGHLIGHT_COLOR if is_highlighted else STROKES_COLOR
        strokes_color = STROKES_COLOR
        fig.add_trace(
            go.Scatter(
                x=pile_df['Time'],
                y=pile_df['Strokes'].round(0),
                mode='lines',
                name='Strokes',
                line=dict(color=strokes_color, width=line_width),
                hoverinfo='x+y+text',
                hovertext=f'Strokes', #Pile {pile_id}:
                legendgroup='Strokes',
                showlegend=(pile_idx == 0),
                opacity=0.8 if not is_highlighted else 1.0,
                customdata=[pile_id] * len(pile_df)
            ),
            secondary_y=False
        )

        # Torque trace (with appropriate color for highlighting)
        # torque_color = HIGHLIGHT_COLOR if is_highlighted else TORQUE_COLOR
        torque_color = TORQUE_COLOR
        fig.add_trace(
            go.Scatter(
                x=pile_df['Time'],
                y=pile_df['Torque'].round(2),
                mode='lines',
                name='Torque',
                line=dict(color=torque_color, width=line_width),
                hoverinfo='x+y+text',
                hovertext=f'Torque', #Pile {pile_id}:
                legendgroup='Torque [ton*meters]',
                showlegend=(pile_idx == 0),
                opacity=0.8 if not is_highlighted else 1.0,
                customdata=[pile_id] * len(pile_df)
            ),
            secondary_y=True
        )

        # Add annotation for this pile
        if not pile_df.empty:
            mid_idx = len(pile_df) // 2
            annotation_time = pile_df['Time'].iloc[mid_idx]
            annotation_depth = -pile_df['Depth'].min() * 0.95 + (pile_idx * 0.5)

            annotations.append(dict(
                x=annotation_time,
                y=annotation_depth,
                xref="x",
                yref="y",
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
        height=400,
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
            x=0.05,
            font=dict(size=11),
            bgcolor='rgba(25, 49, 83, 0.9)',
            bordercolor='rgba(255, 255, 255, 0.3)',
            borderwidth=1
        ),
        annotations=annotations
    )

    # Axes config
    fig.update_yaxes(
        title_text="Depth/Strokes",
        secondary_y=False,
        showgrid=True,
        gridcolor='rgba(255, 255, 255, 0.1)',
        zeroline=False
    )
    fig.update_yaxes(
        title_text="Torque",
        secondary_y=True,
        showgrid=False,
        zeroline=False
    )
    fig.update_xaxes(
        title_text="Time",
        showgrid=True,
        showticklabels=True,
        gridcolor='rgba(255, 255, 255, 0.1)',
        title_standoff=5
    )
    fig.update_xaxes(showspikes=False)
    fig.update_yaxes(showspikes=False)

    return fig


def create_rig_location_chart(index,rig_id, pile_ids, pile_data_dict, df_prop, selected_pile_id=None):
    """Create location chart for a specific rig"""
    fig = go.Figure()

    # Different colors for different rigs
    rig_colors = ['#1E90FF', '#FF6B6B', '#32CD32', '#FFD700', '#9370DB', '#FF6347']
    color = rig_colors[int(index) % len(rig_colors)]

    x_coords = []
    y_coords = []
    pile_ids_list = []
    position = []
    marker_sizes = []
    marker_colors = []

    for order_num, mdict in enumerate(pile_data_dict, start=1):
        pile_id = list(mdict.keys())[0]
        tmp = df_prop[df_prop['PileID'] == pile_id][['XEasting', 'YNorthing']]
        if not tmp.empty:
            x_coords.append(tmp['XEasting'].values[0])
            y_coords.append(tmp['YNorthing'].values[0])
            pile_ids_list.append(pile_id)
            position.append(order_num)

            # Determine marker size and color based on selection
            if selected_pile_id == pile_id:
                marker_sizes.append(20)  # Larger for selected
                marker_colors.append('#FF1493')  # Highlight color
            else:
                marker_sizes.append(12)
                marker_colors.append(color)

    # Add trace for this rig with all points
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='markers+text',
        marker=dict(
            size=marker_sizes,
            color=marker_colors,
            line=dict(width=2, color='white')
        ),
        text=[str(n) for n in position],
        textposition="top center",
        name=f"Rig {rig_id}",
        hovertemplate=(
            '<b>PileID: %{customdata[0]}<br><extra></extra>'
        ),
        customdata=[[pid] for pid in pile_ids_list]
    ))

    # Add arrows for drilling order
    for j in range(len(pile_ids_list) - 1):
        fig.add_annotation(
            x=x_coords[j + 1],
            y=y_coords[j + 1],
            ax=x_coords[j],
            ay=y_coords[j],
            xref="x", yref="y",
            axref="x", ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor=color,
            opacity=0.7
        )

    fig.update_yaxes(showgrid=True, gridcolor="grey")
    fig.update_xaxes(showgrid=True, gridcolor="grey")

    fig.update_layout(
        title=f"Rig {rig_id} - Pile Locations with Drilling Order (Click on a pile to highlight)",
        plot_bgcolor="#193153",
        paper_bgcolor="#193153",
        font_color="white",
        showlegend=True,
        xaxis_title="XEasting",
        yaxis_title="YNorthing",
        height=400
    )
    fig.update_layout(
        xaxis=dict(
            # title='X Axis (10^6 units)',
            tickformat='.1e',
            exponentformat='power',
            showgrid=True
        ),
        yaxis=dict(
            # title='Y Axis (10^6 units)',
            tickformat='.1e',
            exponentformat='power',
            showgrid=True
        ),

    )

    return fig


def apply_custom_aggregation(df,aggregation_type):
    """
    Apply custom aggregation based on grouping type
    """

    if aggregation_type == 'jobno':
        # Find the latest date for each JobNo
        latest_dates = df.groupby('JobNo')['Time'].max().reset_index()

        # Merge to get only the latest entries for each JobNo
        latest_data = pd.merge(df, latest_dates, on=['JobNo', 'Time'], how='inner')

        # Now aggregate by JobNo (summing numeric columns, taking first for others)
        aggregation_rules = {
            'JobName': 'first',
            'RigID': lambda x: ', '.join(sorted(set(x.astype(str)))),
            'Time': 'last',
            'Piles': 'sum',
            'ConcreteDelivered': 'sum',
            'LaborHours': 'sum',
            'DaysRigDrilled': 'sum',
            'AveragePileLength': 'mean',
            'AveragePileWaste': 'mean',
            'AverageRigWaste': 'mean'
        }

        available_columns = [col for col in aggregation_rules.keys() if col in latest_data.columns]
        aggregation_rules = {col: aggregation_rules[col] for col in available_columns}

        grouped_df = latest_data.groupby('JobNo').agg(aggregation_rules).reset_index()

    elif aggregation_type == 'daily':
        # Daily aggregation by JobNo + Date + RigID
        aggregation_rules = {
            'JobName': 'first',
            'Piles': 'sum',
            'ConcreteDelivered': 'sum',
            'LaborHours': 'sum',
            'DaysRigDrilled': 'sum',
            'AveragePileLength': 'mean',
            'AveragePileWaste': 'mean',
            'AverageRigWaste': 'mean',
        }

        available_columns = [col for col in aggregation_rules.keys() if col in df.columns]
        aggregation_rules = {col: aggregation_rules[col] for col in available_columns}

        grouped_df = df.groupby(['JobNo', 'Time']).agg(aggregation_rules).reset_index()

    elif aggregation_type == 'rigid':
        # For RigID: get latest entry for each RigID
        latest_rig_entries = df.sort_values(['RigID', 'Time']).groupby('RigID').tail(1)

        aggregation_rules = {
            'JobNo': 'first',
            'JobName': 'first',
            'Time': 'max',
            'Piles': 'sum',
            'ConcreteDelivered': 'sum',
            'LaborHours': 'sum',
            'DaysRigDrilled': 'sum',
            'AveragePileLength': 'mean',
            'AveragePileWaste': 'mean',
            'AverageRigWaste': 'mean'
        }

        available_columns = [col for col in aggregation_rules.keys() if col in latest_rig_entries.columns]
        aggregation_rules = {col: aggregation_rules[col] for col in available_columns}

        grouped_df = latest_rig_entries.groupby('RigID').agg(aggregation_rules).reset_index()
    elif aggregation_type == 'overall':

        # Overall: Aggregate by Date only (across all jobs and rigs)
        aggregation_rules = {
            'Piles': 'sum',
            'ConcreteDelivered': 'sum',
            'LaborHours': 'sum',
            'DaysRigDrilled': 'sum',
            'AveragePileLength': 'mean',
            'AveragePileWaste': 'mean',
            'AverageRigWaste': 'mean',
            'JobCount': 'nunique',  # Count of unique jobs per day
            'RigCount': 'nunique',  # Count of unique rigs per day
        }

        # Only use columns that exist in the dataframe
        available_columns = [col for col in aggregation_rules.keys() if col in df.columns]
        aggregation_rules = {col: aggregation_rules[col] for col in available_columns}

        # Add count columns if they don't exist
        if 'JobCount' not in df.columns:
            df['JobCount'] = df['JobNo']
        if 'RigCount' not in df.columns:
            df['RigCount'] = df['RigID']

        grouped_df = df.groupby('Time').agg(aggregation_rules).reset_index()

        # Add summary information
        grouped_df['Summary'] = f"Daily Total"
        grouped_df['JobNo'] = "All Jobs"
        grouped_df['RigID'] = "All Rigs"
        grouped_df['JobName'] = "Daily Summary"


    else:
        grouped_df = df.copy()

    return grouped_df



@callback(
    Output("rig-summary-data-grid", "rowData"),
    [Input("grouping-level", "value")]
)
def update_grid(grouping_level):
    # Apply date range filtering
    filtered_df = df_stats.copy()

    if grouping_level == 'none':
        # Show raw data without grouping
        display_df = filtered_df
    else:
        # Determine grouping columns
        if grouping_level == 'daily':
            group_columns = ['Date', 'JobNo', 'RigID']
        elif grouping_level == 'jobno':
            group_columns = ['JobNo']
        elif grouping_level == 'rigid':
            group_columns = ['RigID']

        # Apply custom aggregation
        display_df = apply_custom_aggregation(filtered_df,grouping_level)

    # Select and format columns properly
    col_def = ['JobNo', 'JobName', 'Time', 'RigID', 'Piles', 'ConcreteDelivered',
               'LaborHours', 'DaysRigDrilled',
               'AveragePileLength', 'AveragePileWaste', 'AverageRigWaste']
    display_df[['AveragePileLength', 'AveragePileWaste', 'AverageRigWaste']] = display_df[['AveragePileLength', 'AveragePileWaste', 'AverageRigWaste']].round(1)
    display_df = display_df[col_def]

    # Convert to records - keep numeric values as numbers, not strings
    rows = display_df.to_dict("records")

    return rows


@callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-rigsummary-export-csv", "n_clicks"),
    [State("rig-summary-data-grid", "rowData"),
     State("grouping-level", "value"),
     # State("date-range", "start_date"),
     # State("date-range", "end_date")
     ],
    prevent_initial_call=True
)
def export_to_csv(n_clicks, row_data, grouping_level): #, start_date, end_date
    if n_clicks > 0 and row_data:
        # Convert row data back to DataFrame
        export_df = pd.DataFrame(row_data)

        # Create filename with context
        filename = f"drilling_data"
        if grouping_level != 'none':
            filename += f"_{grouping_level}_grouped"
        # if start_date and end_date:
        #     filename += f"_{start_date}_to_{end_date}"
        filename += ".csv"

        return dcc.send_data_frame(export_df.to_csv, filename, index=False)


# Add this callback to handle clicks on individual location charts
# @callback(
#     Output("rig-charts-container", "children", allow_duplicate=True),
#     [Input(f"pile-location-chart-{i}", "clickData") for i in range(1, 10)],  # Adjust range based on max expected rigs
#     [State("job-table", "selectedRows"),
#      State("date-picker", "date"),
#      State("rig-charts-container", "children")],
#     prevent_initial_call=True
# )
# def handle_pile_click(*args):
#     """Handle click events on any of the rig location charts"""
#     ctx = dash.callback_context
#     if not ctx.triggered:
#         return no_update
#
#     # Extract the triggered input and click data
#     triggered_id = ctx.triggered[0]['prop_id']
#     click_data = ctx.triggered[0]['value']
#
#     # Get the states (selected_rows, selected_date, current_children)
#     selected_rows = args[-3]  # Adjust indices based on your actual state order
#     selected_date = args[-2]
#     current_children = args[-1]
#
#     if not selected_rows or not click_data:
#         return no_update
#
#     # Recreate the charts with the selected pile highlighted
#     return update_rig_charts(selected_rows, selected_date, click_data, current_children)

