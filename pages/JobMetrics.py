
from dash import dcc, html, Output, Input, State, callback,no_update,ctx
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
# from dash.exceptions import PreventUpdate
# import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import os
# import base64
import dash
import dash_ag_grid as dag
from datetime import date

dash.register_page(
    __name__,
    path_template="/Metrics",
    path="/Metrics",
)

assets_path = os.path.join(os.getcwd(), "assets")
summary_folder = os.path.join(assets_path, 'data','Summary')

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
        try:
            jobnumber = int(f.split('-')[0])
            jobs.append(jobnumber)
        except:
            try:
                jobnumber_design = int(f.split('_')[0])
            except:
                continue
        if not jobnumber is None:
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
        df_todate_tot = df_todate.groupby('Time').sum()

        time_interval = pd.to_datetime(df_todate_tot.index)
        df_todate_tot['Piles%'] = df_todate_tot['Piles']/df_design['COUNT'].sum()
        df_todate_tot['Concrete%'] = df_todate_tot['ConcreteDelivered']/df_design['TOTAL CONCRETE  (CY)'].sum()
        df_todate_tot['RigDays%'] = df_todate_tot['DaysRigDrilled']/df_design['RIG DAYS '].sum()
        df_todate_tot['LaborHours%'] = df_todate_tot['LaborHours']/df_design['Man Hours Needed'].sum()
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

        rows.append({
            "JobNumber": job,
            "StatusSymbol": status_symbol,
            "StatusColor": status,
            "Piles %": f"{current['Piles%']*100:.1f}%",
            "Concrete %": f"{current['Concrete%']*100:.1f}%",
            "Rig Days %": f"{current['RigDays%']*100:.1f}%",
            "Labor Hours %": f"{current['LaborHours%']*100:.1f}%",

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
    {"headerName": "Piles %", "field": "Piles %"},
    {"headerName": "Concrete %", "field": "Concrete %"},
    {"headerName": "Rig Days %", "field": "Rig Days %"},
    {"headerName": "Labor Hours %", "field": "Labor Hours %"},
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
    # html.H3("Performance Dashboard",style={"color": "white", "marginBottom": "10px"}),
    dcc.DatePickerSingle(
        id="date-picker",
        date=date.today(),
        display_format="YYYY-MM-DD",
        style=date_picker_style,
        className="dash-datepicker",


    ),
    html.Div(id="summary-cards", style={"display": "flex", "gap": "20px", "marginTop": "20px"}),
    html.Br(),
    dcc.Graph(id="job-bar-chart",style={"backgroundColor": "#193153", 'width': '100%', 'marginBottom': '5px','marginTop': '5px','height': '500px'},),
    html.Br(),
    html.Div(
        dag.AgGrid(
            id="job-table",
            columnDefs=column_defs,
            rowData=[],
            defaultColDef={"resizable": True, "sortable": True, "filter": True, "cellStyle": {"textAlign": "center"}},
            dashGridOptions={"rowSelection": "single"},

        style={"height": "300px", "width": "100%"},

        className="ag-theme-alpine-dark",
        ),
        style={"marginTop": "20px"}
    ),
    html.Br(),
    dcc.Graph(id="job-pie",style={"backgroundColor": "#193153", 'width': '100%', 'marginBottom': '5px','height': '500px'},),
], style={'backgroundColor': '#193153', 'height': '550vh', 'padding': '20px', 'position': 'relative'})


@callback(
    Output("job-table", "rowData"),
    Output("summary-cards", "children"),
    Input("date-picker", "date")
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
        html.Div(f"Total Piles Drilled: {total_piles:.0f}", style={"padding": "10px", "background": "#d4edda", "borderRadius": "8px", "flex": "1"}),
        html.Div(f"Total Concrete: {total_concrete:.1f} CY", style={"padding": "10px", "background": "#cce5ff", "borderRadius": "8px", "flex": "1"}),
        html.Div(f"Total Rig Days: {total_rig_days:.1f}", style={"padding": "10px", "background": "#fff3cd", "borderRadius": "8px", "flex": "1"}),
        html.Div(f"Total Man Hours: {total_labor_hours:.0f}", style={"padding": "10px", "background": "#f8d7da", "borderRadius": "8px", "flex": "1"})
    ]

    return table_rows, cards

# layout = html.Div([
#     dag.AgGrid(
#         id="job-table",
#         columnDefs=column_defs,
#         rowData=table_rows,
#         defaultColDef={"resizable": True, "sortable": True, "filter": True, "cellStyle": {"textAlign": "center"}},
#         style={"height": "300px", "width": "100%"},
#
#         className="ag-theme-alpine-dark",
#     )
# ], style={'backgroundColor': '#193153', 'height': '550vh', 'padding': '20px', 'position': 'relative'})
#
@callback(
    Output("job-bar-chart", "figure"),
    Input("date-picker", "date"),
)
def update_job_bar_chart(selected_date):
    # Get filtered data from your summary_metrics
    records = []
    for job, df in summary_metrics.items():
        df_to_date = df[df['Time']<=pd.to_datetime(selected_date)]
        row = df_to_date.iloc[-1]
        records.append({
            "JobNumber": job,
            "Piles %": round(row["Piles%"] * 100,2),
            "Concrete %": round(row["Concrete%"] * 100,2),
            "Rig Days %": round(row["RigDays%"] * 100,2),
            "Labor Hours %": round(row["LaborHours%"] * 100,2)
        })

    if not records:
        return px.bar(title="No data available for selected date")

    df_chart = pd.DataFrame(records)

    # Melt dataframe so Plotly can group bars
    df_melted = df_chart.melt(id_vars="JobNumber",
                              value_vars=["Piles %", "Concrete %", "Rig Days %", "Labor Hours %"],
                              var_name="Metric",
                              value_name="Percent")

    fig = px.bar(
        df_melted,
        x="JobNumber",
        y="Percent",
        color="Metric",
        barmode="group",
        text="Percent",
        title=f"Job Performance Metrics at {selected_date}"
    )

    fig.update_layout(
        yaxis_title="Percent (%)",
        xaxis_title="Job Number",
        legend_title="Metric",
        template="plotly_white"
    )

    fig.update_layout(
        plot_bgcolor="#193153",
        paper_bgcolor="#193153",
        font=dict(color="white"),
        showlegend=True,
        dragmode="select",
        margin=dict(l=50, r=50, b=50, t=50, pad=4),
        autosize = False,
        height = 600
    )

    return fig


@callback(
    Output("job-pie", "figure"),
    Input("job-table", "selectedRows"),
    Input("date-picker", "date"),prevent_initial_call=True
)


def update_pie(selected_rows,selected_date):
    if not selected_rows:
        # return px.pie(title="Select a row to see details")
        return go.Figure(layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"})

    row = selected_rows[0]  # Get the selected row's data
    df_daily = prepare_time_spent_stats(summary_dic_daily)
    # Filter by JobID and date
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
        piles  = str(rig_data['Piles'].values[0])
        values = [
            rig_data['MoveTime'].sum(),
            rig_data['DrillTime'].sum(),
            rig_data['GroutTime'].sum(),
            rig_data['InstallTime'].sum(),
            rig_data['DelayTime'].sum(),
        ]
        labels = ["MoveTime", "DrillTime", "GroutTime", "InstallTime", "DelayTime"]

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