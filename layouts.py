from dash import dcc
from dash import html
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import dash
from dash import dash_table
# from dash.dash_table.Format import Group, Format
# import dash_table.FormatTemplate as FormatTemplate
from datetime import datetime as dt
# from main import app
import dash_ag_grid as dag

import dash_bootstrap_components as dbc
####################################################################################################
# 000 - DEFINE REUSABLE COMPONENTS AS FUNCTIONS
####################################################################################################

#####################
# Header with logo
def get_header():
    title_text = "Morris-Shea Drilling App"
    header = html.Div([
        dbc.Row([
            dbc.Col(
                html.H1(title_text, style={'color': 'white'}),
                xs=12, sm=8, md=8, lg=6, xl=6,
                style={'textAlign': 'center','marginBottom':'10px'}
            ),
            dbc.Col(
                html.Img(src="/assets/MSB.logo.JPG", style={'height': '70px', 'maxWidth': '100%', 'width': 'auto'}),
                xs=12, sm=4, md=4, lg=6, xl=6,
                style={'textAlign': 'center'}
            ),
        ],
            align="center", justify="between", className="g-0")
    ],
        style={'padding': '10px', 'backgroundColor': '#193153'})

    return header

#####################
# Nav bar
def get_navbar():

    navbar = html.Div([

        html.Div([], className = 'col-3'),

        html.Div([
            dcc.Link(
                html.H4(children = 'Job Overview',
                        style = ""),
                href='/apps/job_overview'
                )
        ],
        className='col-2'),

        html.Div([
            dcc.Link(
                html.H4(children = 'DailySummary'),
                href='/apps/daily_summary'
                )
        ],
        className='col-2'),

        html.Div([
            dcc.Link(
                html.H4(children = 'PileList'),
                href='/apps/pile_list'
                )
        ],
        className='col-2'),

        html.Div([], className = 'col-3')

    ],
    className = 'row',
    style = {'background-color' :  '#193153',
            'box-shadow': '2px 5px 5px 1px rgba(255, 101, 131, .5)'}
    )


    return navbar

#####################
# Empty row

def get_emptyrow(h='45px'):
    """This returns an empty row of a defined height"""

    emptyrow = html.Div([
        html.Div([
            html.Br()
        ], className = 'col-12')
    ],
    className = 'row',
    style = {'height' : h})

    return emptyrow


def get_filters(properties_df):
    filters = html.Div([
        dbc.Row([
            dbc.Col(dcc.Dropdown(
                id="jobid-filter",
                options=[{"label": str(r), "value": str(r)} for r in properties_df["JobID"].dropna().unique()],
                placeholder="Filter by JobID",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            ),xs=10, sm=5, md=8, lg=6, xl=5),

            dbc.Col(dcc.Dropdown(
                id="date-filter",
                options=[{"label": d, "value": d} for d in sorted(properties_df["date"].unique())],
                placeholder="Select a Date",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            ),xs=10, sm=5, md=8, lg=6, xl=5),
            dbc.Col(dcc.Dropdown(
                id="rigid-filter",
                options=[{"label": str(r), "value": str(r)} for r in properties_df["RigID"].dropna().unique()],
                placeholder="Filter by RigID",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            ),xs=10, sm=5, md=8, lg=6, xl=5),
            dbc.Col(dcc.Dropdown(
                id="pileid-filter",
                options=[{"label": str(p), "value": str(p)} for p in properties_df["PileID"].dropna().unique()],
                placeholder="Filter by PileID",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            ),xs=10, sm=5, md=8, lg=6, xl=5)
        #     close first row with 4 drop down
            ]),

        dbc.Row([
                dbc.Col(dcc.Dropdown(
                    id="pilecode-filter",
                    options=[{"label": str(r), "value": str(r)} for r in properties_df["PileCode"].dropna().unique()],
                    placeholder="Filter by PileCode",
                    style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                    className="dark-dropdown"
                 ),xs=10, sm=5, md=8, lg=6, xl=5),
            dbc.Col(dcc.Dropdown(
                id="productcode-filter",
                options=[{"label": str(r), "value": str(r)} for r in properties_df["ProductCode"].dropna().unique()],
                placeholder="Filter by ProductCode",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            ),xs=10, sm=5, md=8, lg=6, xl=5),
            #
            dbc.Col(dcc.Dropdown(
                id="piletype-filter",
                options=[{"label": str(r), "value": str(r)} for r in properties_df["PileType"].dropna().unique()],
                placeholder="Filter by PileType",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            ),xs=10, sm=5, md=8, lg=6, xl=5),

            dbc.Col(dcc.Dropdown(
                id="pilestatus-filter",
                options=[{"label": str(r), "value": str(r)} for r in properties_df["PileStatus"].dropna().unique()],
                placeholder="Filter by PileStatus",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            ),xs=10, sm=5, md=8, lg=6, xl=5),
    #     close second row
            ]),
    # close html.Div
    ], style={'marginBottom': '10px', 'display': 'flex', 'justifyContent': 'center'})


    return filters


def get_pilelist():

   pileList =  html.Div([
        # Map Section
        dbc.Button("Show Pile List", id="toggle-pilelist", color="primary", className="mb-2"),
        dbc.Collapse(
            [
                dag.AgGrid(
                    id="pilelist-table",
                    columnDefs=[
                        {"headerName": "Time", "field": "Time", "sortable": True, "filter": True},
                        {"headerName": "JobID", "field": "JobID", "sortable": True, "filter": True},
                        {"headerName": "PileID", "field": "PileID", "sortable": True, "filter": True},
                        {"headerName": "LocationID", "field": "LocationID", "sortable": True, "filter": True},
                        {"headerName": "PileStatus", "field": "PileStatus", "sortable": True, "filter": True, "editable": True,"cellEditor": "agSelectCellEditor",
                        "cellEditorParams": {"values": ["Complete", "Abandoned"]},},
                        {"headerName": "PileType", "field": "PileType", "sortable": True, "filter": True, "editable": True,
                            "cellEditor": "agSelectCellEditor", "cellEditorParams": {"values": ["1", "2", "3", "3A", "4", "5"]},},
                        {"headerName": "Distance", "field": "Distance", "sortable": True, "filter": True, "editable": True},
                        {"headerName": "MoveTime", "field": "MoveTime", "sortable": True, "filter": True, "editable": True},
                        {"headerName": "DelayTime", "field": "DelayTime", "sortable": True, "filter": True, "editable": True},
                        {"headerName": "Totaltime", "field": "Totaltime", "sortable": True, "filter": True, "editable": True},
                        {"headerName": "MinDepth", "field": "MinDepth", "sortable": True, "filter": True,"editable": True},
                        {"headerName": "MaxStrokes", "field": "MaxStrokes", "sortable": True, "filter": True,"editable": True},
                        {"headerName": "OverBreak", "field": "OverBreak", "sortable": True, "filter": True,"editable": False},
                        {"headerName": "PumpID", "field": "PumpID", "sortable": True, "filter": True, "editable": True},
                        {"headerName": "Calibration", "field": "Calibration", "sortable": True, "filter": True, "editable": True},
                        {"headerName": "Comments", "field": "Comments", "sortable": True, "filter": True, "editable": True},
                        {"headerName": "Delay", "field": "Delay", "sortable": True, "filter": True, "editable": True,
                         "cellEditor": "agSelectCellEditor", "cellEditorParams": {"values": ['Waiting on Concrete', 'Site access', 'Layout','Other']},},
                    ],
                    rowData=[],  # Initially empty
                    defaultColDef={"resizable": True, "sortable": True, "filter": True, "editable": True},
                    className="ag-theme-alpine-dark",
                    dashGridOptions={
                            'undoRedoCellEditing': True,
                            'undoRedoCellEditingLimit': 20}
                ),
                # Print Button
                html.Button("Download Pile List", id="btn_download", n_clicks=0),
                # ,style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between','marginLeft': '5px'}
                html.Button("Save changes", id="btn_save", n_clicks=0,style={'marginLeft': '5px'}),
                dcc.Download(id="download-csv")
            ],
            id="collapse-pilelist",
            is_open=False
        ),


    ], style={"backgroundColor": "#193153"})

   return pileList

def get_filtered_table():
    filterd_table = html.Div([dag.AgGrid(
                        id="filtered-table",
                        columnDefs=[
                        {"headerName": "Field", "field": "Field", "sortable": True, "filter": True},
                        {"headerName": "Value", "field": "Value", "sortable": True, "filter": True},],
                        rowData = [],  # Initially empty
                        defaultColDef = {"resizable": True, "sortable": True, "filter": True, "editable": True}, \
                        className = "ag-theme-alpine-dark",
                        # columnSize="autoSize",
                        )])
    return  filterd_table
def get_pile_details_cards(title,move_time,move_distance,delay_time,overbreak):
    details = html.Div([
        html.H5(title),
        dbc.Row([
            dbc.Col(
                html.Div([
                    html.Div("⏳ Move Time", style={"fontWeight": "bold", "fontSize": "14px"}),
                    html.Div(move_time, style={"fontSize": "14px", "color": "white"})
                ], style={"padding": "5px", "textAlign": "center"}),
                xs=6, sm=5, md=6, lg=3, xl=3
            ),
            dbc.Col(
                html.Div([
                    html.Div("📐 Distance", style={"fontWeight": "bold", "fontSize": "14px"}),
                    html.Div(move_distance, style={"fontSize": "14px", "color": "white"})
                ], style={"padding": "5px", "textAlign": "center"}),
                xs=6, sm=5, md=6, lg=3, xl=3
            ),
            dbc.Col(
                html.Div([
                    html.Div("⏰ Delay Time", style={"fontWeight": "bold", "fontSize": "14px"}),
                    html.Div(delay_time, style={"fontSize": "14px", "color": "white"})
                ], style={"padding": "5px", "textAlign": "center"}),
                xs=6, sm=5, md=6, lg=3, xl=3
            ),
            dbc.Col(
                html.Div([
                    html.Div("🚧 OverBreak", style={"fontWeight": "bold", "fontSize": "14px"}),
                    html.Div(overbreak, style={"fontSize": "14px", "color": "white"})
                ], style={"padding": "5px", "textAlign": "center", }),
                xs=6, sm=5, md=6, lg=3, xl=3
            ),
        ], className="g-2")
    ], style={'padding': '20px'})

    return details
