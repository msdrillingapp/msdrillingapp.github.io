
from dash import dcc, html, Output, Input, State, callback,no_update,ctx, MATCH, ALL

from dash.exceptions import PreventUpdate
import pandas as pd
import os
import dash
import dash_ag_grid as dag
from datetime import date,timedelta, datetime
from collections import defaultdict
import dash_bootstrap_components as dbc
from data_loader import ensure_data_loaded
from functools import lru_cache


dash.register_page(
    __name__,
    path_template="/RS_Report",
    path="/RS_Report",
)

assets_path = os.path.join(os.getcwd(), "assets")
summary_folder = os.path.join(assets_path, 'data','Summary')

col_def = ['RigID','Date','JobID','Piles','TurnStartTime','AvgPileLength','PileWaste','RigWaste','TurnEndTime','LaborHours']
def get_data_summary(value:str):
    data = ensure_data_loaded()
    return data[value]

@lru_cache(maxsize=8)
def load_data_metrics():
    my_jobs = get_data_summary('my_jobs')
    df_stats_daily = pd.DataFrame()
    for jb,job in my_jobs.jobs.items():
         tmp = job.daily_stats
         tmp['JobID'] = job.job_full_id
         df_stats_daily = pd.concat([df_stats_daily,tmp],ignore_index=True)

    df_stats_daily.rename(columns={'Time':'Date','mean_PileLength':'AvgPileLength'},inplace=True)
    df_stats_daily['TurnStartTime'] = pd.to_datetime(df_stats_daily['TurnStartTime']).dt.time
    df_stats_daily['TurnEndTime'] = pd.to_datetime(df_stats_daily['TurnEndTime']).dt.time
    col_round_1 = ['AvgPileLength']
    for col in col_round_1:
        df_stats_daily[col] = df_stats_daily[col].astype(float).round(1)
    col_round_3 = ['PileWaste', 'RigWaste']
    for col in col_round_3:
        df_stats_daily[col] = df_stats_daily[col].astype(float).round(2)

    return df_stats_daily[col_def].sort_values(by=['Date','JobID','RigID'],ascending=[False,True,True])[df_stats_daily['Piles']>0]

col_def = ['RigID','Date','JobID','Piles','TurnStartTime','AvgPileLength','PileWaste','RigWaste','TurnEndTime','LaborHours']

cols = ['RigID','Date','JobID','Piles']
column_defs = [
    {"headerName": col, "field": col, "filter": True,
     "enableRowGroup": True}
    for col in cols
]
column_defs.extend([
             {"headerName": 'Turn Start Time', "field": 'TurnStartTime', "filter": True, "enableRowGroup": True},
             {"headerName": 'Avg Pile Length', "field": 'AvgPileLength', "filter": True,"enableRowGroup": True},
             {"headerName": 'Pile Waste', "field": 'PileWaste', "filter": True,"enableRowGroup": True},
             {"headerName": 'Rig Waste', "field": 'RigWaste', "filter": True,"enableRowGroup": True},
             {"headerName": 'Turn End Time', "field": 'TurnEndTime', "filter": True, "enableRowGroup": True},
                   ])

df_stats_daily = load_data_metrics()

layout = html.Div([
    dag.AgGrid(
        id="rs-data-grid",
        columnDefs=column_defs,
        rowData=df_stats_daily.to_dict("records"),
        className="ag-theme-alpine-dark",
        columnSize="sizeToFit",
        defaultColDef={
            "resizable": True,
            "sortable": True,
            "filter": True,
            "minWidth": 100,
            "wrapHeaderText": True,
            "autoHeaderHeight": True,
        },
        dashGridOptions={
            "rowSelection": "single",
            "pagination": True,
            "paginationPageSize": 50,
            "enableRangeSelection": True,
            "enableCharts": True,
            "animateRows": False,
            "enableSorting": True,
            "enableFilter": True,
            "enableRangeHandle": True,
            "ensureDomOrder": True,
            "suppressDragLeaveHidesColumns": True,
            "maintainColumnOrder": True,
            # ✅ Automatically size columns when defs update
            "onFirstDataRendered": {"function": "params.api.sizeColumnsToFit();"},
            "onColumnDefsChanged": {"function": "params.api.sizeColumnsToFit();"},

        },

        style={"height": "600px", "width": "100%", "marginTop": '5px'}
    ),
    html.Button(
        "Download CSV",
        id="btn-download-csv-rs-report",
        n_clicks=0,
        className="grouping-button",
        style={'marginTop': '5px'}
    ),
    dcc.Download(id="download-dataframe-csv-rs-report"),
],style={
        'backgroundColor': '#193153',
        'minHeight': '500vh',
        'padding': '20px'
    })



@callback(
    Output("download-dataframe-csv-rs-report", "data"),
    Input("btn-download-csv-rs-report", "n_clicks"),
    [State("rs-data-grid", "rowData")],
    prevent_initial_call=True
)
def download_csv(n_clicks, row_data):
    if not row_data:
        return dash.no_update

    if n_clicks > 0 and row_data:
        # Convert row data back to DataFrame
        export_df = pd.DataFrame(row_data)
    # Create filename with context
    filename = f"RS_summary_"
    # if grouping_level != 'none':
    #     filename += f"_{grouping_level}_grouped_"
    date_str = datetime.now().strftime(("%Y/%m/%d, %H:%M:%S"))
    filename += date_str+".csv"

    return dcc.send_data_frame(export_df.to_csv, filename, index=False)