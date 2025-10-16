from dash import dcc
from dash import html
from datetime import datetime as dt
import dash_ag_grid as dag
import dash_daq as daq
import dash_bootstrap_components as dbc
import os
from data_loader import get_data, ensure_data_loaded
# from auth_utils import get_accessible_jobs, has_job_access
####################################################################################################
# 000 - DEFINE REUSABLE COMPONENTS AS FUNCTIONS
####################################################################################################
assets_path = os.path.join(os.getcwd(), "assets")
geojson_folder = os.path.join(assets_path, 'data')
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
def get_data_summary(value:str):
    data = ensure_data_loaded()
    return data[value]

def get_filters(): #results_MWD

    # Load data only when needed in callbacks
    my_jobs = get_data_summary('my_jobs')
    job_jonname = {}
    for jb, job in my_jobs.jobs.items():
        job_jonname[jb] = job.job_name
    # if not data['result_MWD']:  # Data not loaded yet
    #     data = ensure_data_loaded()  # Load it now
    # results_MWD = data['result_MWD']
    filters = html.Div([
        dbc.Row([
            dbc.Col(dcc.Dropdown(
                id="jobid-filter",
                # options=[{"label": str(r), "value": str(r)} for r in properties_df["JobNumber"].dropna().unique()],
                options=[{"label": str(r)+'-'+job_jonname[r], "value": str(r)} for r in job_jonname.keys()],
                # options=[{"label": str(r), "value": str(r)} for r in accessible_jobs],
                placeholder="Filter by JobName",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px','fontSize': '11px'},
                className="dark-dropdown"
            ),xs=10, sm=5, md=8, lg=6, xl=5),

            dbc.Col(dcc.Dropdown(
                id="date-filter",
                # options=[{"label": d, "value": d} for d in sorted(properties_df["date"].unique())],
                placeholder="Select a Date",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            ),xs=10, sm=5, md=8, lg=6, xl=5),
            dbc.Col(dcc.Dropdown(
                id="rigid-filter",
                options=[],
                # options=[{"label": str(r), "value": str(r)} for r in properties_df["RigID"].dropna().unique()],
                placeholder="Filter by RigID",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            ),xs=10, sm=5, md=8, lg=6, xl=5),
            dbc.Col(dcc.Dropdown(
                id="pileid-filter",
                # options=[{"label": str(p), "value": str(p)} for p in properties_df["PileID"].dropna().unique()],
                options=[],
                placeholder="Filter by PileID",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            ),xs=10, sm=5, md=8, lg=6, xl=5)
        #     close first row with 4 drop down
            ]),

        dbc.Row([
                dbc.Col(dcc.Dropdown(
                    id="pilecode-filter",
                    # options=[{"label": str(r), "value": str(r)} for r in properties_df["PileCode"].dropna().unique()],
                    options=[],
                    placeholder="Filter by PileCode",
                    style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                    className="dark-dropdown"
                 ),xs=10, sm=5, md=8, lg=6, xl=5),
            dbc.Col(dcc.Dropdown(
                id="productcode-filter",
                # options=[{"label": str(r), "value": str(r)} for r in properties_df["ProductCode"].dropna().unique()],
                options=[],
                placeholder="Filter by ProductCode",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            ),xs=10, sm=5, md=8, lg=6, xl=5),
            #
            dbc.Col(dcc.Dropdown(
                id="piletype-filter",
                # options=[{"label": str(r), "value": str(r)} for r in properties_df["PileType"].dropna().unique()],
                options=[],
                placeholder="Filter by PileType",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            ),xs=10, sm=5, md=8, lg=6, xl=5),

            dbc.Col(dcc.Dropdown(
                id="pilestatus-filter",
                # options=[{"label": str(r), "value": str(r)} for r in properties_df["PileStatus"].dropna().unique()],
                options=[],
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

   pileList = html.Div([
        # Map Section
        dbc.Button("Show Pile List", id="toggle-pilelist", color="primary", className="mb-2"),
        dbc.Collapse(
            [
                dag.AgGrid(
                    id="pilelist-table",
                    columnDefs=[
                        {"headerName": "PileID", "field": "PileID", "sortable": True, "filter": True, "pinned": "left"},
                        {"headerName": "Date", "field": "Date", "sortable": True, "filter": True,"hide": True},
                        {"headerName": "Time", "field": "Time", "sortable": True, "filter": True},
                        {"headerName": "JobNumber", "field": "JobNumber", "sortable": True, "filter": True, "hide": True},
                        {"headerName": "JobName", "field": "JobName", "sortable": True, "filter": True,"hide": True},
                        {"headerName": "LocationID", "field": "LocationID", "sortable": True, "filter": True,"headerClass": "header-red" },
                        {"headerName": "MinDepth", "field": "MinDepth", "sortable": True, "filter": True,"editable": True,"headerClass": "header-red"},
                        {"headerName": "MaxStroke", "field": "MaxStrokes", "sortable": True, "filter": True, "editable": True,"headerClass": "header-red"},
                        {"headerName": "OverBreak", "field": "OverBreak", "sortable": True, "filter": True,"editable": False},
                        {"headerName": "PileStatus", "field": "PileStatus", "sortable": True, "filter": True, "editable": True,"cellEditor": "agSelectCellEditor",
                        "cellEditorParams": {"values": ["Complete", "Abandoned"]},"headerClass": "header-red"},
                        {"headerName": "PileCode", "field": "PileCode", "sortable": True, "filter": True,"editable": True, "cellEditor": "agSelectCellEditor",
                         "cellEditorParams": {"values": ["Production Pile", "Test Pile","Recation Pile","Probe"]},"headerClass": "header-red" },
                        {"headerName": "Comments", "field": "Comments", "sortable": True, "filter": True, "editable": True,"headerClass": "header-red"},
                        {"headerName": "DelayTime[min]", "field": "DelayTime", "sortable": True, "filter": True, "editable": False},
                        {"headerName": "DelayReason", "field": "Delay", "sortable": True, "filter": True, "editable": True,
                         "cellEditor": "agSelectCellEditor", "cellEditorParams": {"values": ['Waiting on Concrete', 'Site access', 'Layout','Other']},"headerClass": "header-red"},
                         {"headerName": "PumpID", "field": "PumpID", "sortable": True, "filter": True, "editable": True,"headerClass": "header-red"},
                        {"headerName": "Calibration", "field": "Calibration", "sortable": True, "filter": True, "editable": True,"headerClass": "header-red"},
                        {"headerName": "PileType", "field": "PileType", "sortable": True, "filter": True, "editable": False,
                            "cellEditor": "agSelectCellEditor", "cellEditorParams": {"values": ["1", "2", "3", "3A", "4", "5"]},},
                        {"headerName": "Distance", "field": "Distance", "sortable": True, "filter": True, "editable": False},
                        {"headerName": "MoveTime[min]", "field": "MoveTime", "sortable": True, "filter": True, "editable": False},
                        {"headerName": "TotalTime", "field": "TotalTime", "sortable": True, "filter": True, "editable": False,'hide':True},
                        {"headerName": "InstallTime[min]", "field": "InstallTime", "sortable": True, "filter": True,"editable": False},

                        {"headerName": "RigID", "field": "RigID", "sortable": True, "filter": True, "hide": True},
                        {"headerName": "Client", "field": "Client", "sortable": True, "filter": True, "hide": True},
                        {"headerName": "DrillStartTime", "field": "DrillStartTime", "sortable": True, "filter": True, "hide": True},
                        {"headerName": "DrillEndTime", "field": "DrillEndTime", "sortable": True, "filter": True, "hide": True},
                        {"headerName": "PileLength", "field": "PileLength", "sortable": True, "filter": True,"hide": True},
                        {"headerName": "PileDiameter [in]", "field": "PileDiameter", "sortable": True, "filter": True, "hide": False},
                        {"headerName": "DesignNotes", "field": "DesignNotes", "sortable": False, "filter": True,"hide": False},
                        # {"headerName": "TargetDepth", "field": "TargetDepth", "sortable": False, "filter": True, "hide": False},

                    ],
                    rowData=[],  # Initially empty
                    defaultColDef={"resizable": True, "sortable": True, "filter": True, "editable": True},
                    className="ag-theme-alpine-dark",
                    dashGridOptions={
                            "rowSelection": "single",
                            "animateRows": True,
                            'undoRedoCellEditing': True,
                            'undoRedoCellEditingLimit': 20,
                            # "suppressRowHoverHighlight": True,
                            # "suppressColumnMoveAnimation": True,
                            # "suppressDragLeaveHidesColumns": True,
                            # "suppressLoadingOverlay": True,
                            # "suppressMenuHide": True,
                            # "rowBuffer": 20,  # Only render rows close to visible area
                            # "cacheBlockSize": 20,
                            # "maxBlocksInCache": 5
                        },
                    columnSize = "sizeToFit",
                ),

                # Print Button
                html.Button("Download Pile List", id="btn_download", n_clicks=0),
                # ,style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between','marginLeft': '5px'}
                # html.Button("Save changes", id="btn_save", n_clicks=0,style={'marginLeft': '5px'}),
                dcc.Download(id="download-csv"),
                # html.Button("Go to CPT charts", id='go-button'),
                # dcc.Store(id='shared-data', storage_type='session')

                # html.Button("Download PDF for ALL PileID", id='download-ALL-pdf-btn', disabled=False,style={'marginLeft': '5px'}),
                # dcc.Download(id="download-ALL-pdf"),
                # dcc.Interval(id="poll-interval", interval=1000, n_intervals=0, disabled=True),
                # dcc.Store(id="task-id"),
                # html.Div(id="task-status"),

            ],
            id="collapse-pilelist",
            is_open=False
        ),

    ], style={"backgroundColor": "#193153"})

   return pileList

def get_filtered_table():
    filterd_table = html.Div([dbc.Row([
                dbc.Col(dag.AgGrid(
                        id="filtered-table",
                        columnDefs=[
                        {"headerName": "Field", "field": "Field", "sortable": True, "filter": True},
                        {"headerName": "Value", "field": "Value", "sortable": True, "filter": True},],
                        rowData = [],  # Initially empty
                        defaultColDef = {"resizable": True, "sortable": True, "filter": True, "editable": True}, \
                        className = "ag-theme-alpine-dark",
                        columnSize="sizeToFit",
                        dashGridOptions={
                            "rowSelection": "single",
                            "animateRows": False,  # Disable animations
                            "suppressRowHoverHighlight": True,
                            "suppressColumnMoveAnimation": True,
                            "suppressDragLeaveHidesColumns": True,
                            "suppressLoadingOverlay": True,
                            "suppressMenuHide": True,
                            "rowBuffer": 20,  # Only render rows close to visible area
                            "cacheBlockSize": 20,
                            "maxBlocksInCache": 5
                        }
                        # columnSize="autoSize",
                        ),xs=12, sm=12, md=8, lg=6, xl=6)])],
    )
    return  filterd_table
def get_pile_details_cards(title,move_time,move_distance,delay_time,overbreak,installtime,cycletime,PileLength):
    details = html.Div([
        html.H5(title),
        dbc.Row([
            dbc.Col(
                html.Div([
                    html.Div("⏳ Move Time", style={"fontWeight": "bold", "fontSize": "14px"}),
                    html.Div(move_time, style={"fontSize": "14px", "color": "white"})
                ], style={"padding": "2px", "textAlign": "center"}),
                xs=6, sm=5, md=6, lg=1, xl=1
            ),
            dbc.Col(
                html.Div([
                    html.Div("📐 Distance", style={"fontWeight": "bold", "fontSize": "14px"}),
                    html.Div(move_distance, style={"fontSize": "14px", "color": "white"})
                ], style={"padding": "5px", "textAlign": "center"}),
                xs=6, sm=5, md=6, lg=1, xl=1
            ),
            dbc.Col(
                html.Div([
                    html.Div("⏳ Install Time", style={"fontWeight": "bold", "fontSize": "14px"}),
                    html.Div(installtime, style={"fontSize": "14px", "color": "white"})
                ], style={"padding": "5px", "textAlign": "center"}),
                xs=6, sm=5, md=6, lg=1, xl=1
            ),
            dbc.Col(
                html.Div([
                    html.Div("⏳ Cycle Time", style={"fontWeight": "bold", "fontSize": "14px"}),
                    html.Div(cycletime, style={"fontSize": "14px", "color": "white"})
                ], style={"padding": "5px", "textAlign": "center"}),
                xs=6, sm=5, md=6, lg=1, xl=1
            ),
            dbc.Col(
                html.Div([
                    html.Div("📐 Length", style={"fontWeight": "bold", "fontSize": "14px"}),
                    html.Div(PileLength, style={"fontSize": "14px", "color": "white"})
                ], style={"padding": "5px", "textAlign": "center"}),
                xs=6, sm=5, md=6, lg=1, xl=1
            ),
            dbc.Col(
                html.Div([
                    html.Div("⏰ Delay Time", style={"fontWeight": "bold", "fontSize": "14px"}),
                    html.Div(delay_time, style={"fontSize": "14px", "color": "white"})
                ], style={"padding": "5px", "textAlign": "center"}),
                xs=6, sm=5, md=6, lg=1, xl=1
            ),
            dbc.Col(
                html.Div([
                    html.Div("🚧 OverBreak", style={"fontWeight": "bold", "fontSize": "14px"}),
                    html.Div(overbreak, style={"fontSize": "14px", "color": "white"})
                ], style={"padding": "5px", "textAlign": "center", }),
                xs=6, sm=5, md=6, lg=1, xl=1
            ),
        ], className="g-2")
    ], style={'padding': '5px',"textAlign": "left", })

    return details

def add_charts():
    charts = dbc.Collapse(
            html.Div([
                # Statistics Info Cards
                # html.Div(id="pile-summary-cards", style={
                #     'display': 'flex', 'justifyContent': 'space-around', 'alignItems': 'left',
                #     'backgroundColor': '#193153', 'color': 'white', 'padding': '10px',
                #     'borderRadius': '5px', 'marginTop': '10px'
                # }),
                html.Div(id="pile-summary-cards", style={
                    'display': 'flex',
                    'justifyContent': 'flex-start',  # Changed from 'space-around' to 'flex-start'
                    'alignItems': 'left',
                    'backgroundColor': '#193153',
                    'color': 'white',
                    'padding': '10px',
                    'borderRadius': '5px',
                    'marginTop': '10px',
                    'gap': '20px'  # Optional: Add spacing between cards
                }),

                html.Button("Download PDF for PileID", id='download-pdf-btn', disabled=True),
                dbc.Row([
                    dbc.Col(
                            dcc.Graph(id="time_graph", style={"backgroundColor": "#193153",'width': '100%','margin':'0','height': '400px'}),#
                    xs=12, sm=12, md=12, lg=12, xl=12),
                    # ],className="g-0" ),
                # dbc.Row([
                    dbc.Col(
                        dcc.Graph(id="depth_graph", style={"backgroundColor": "#193153",'margin':'0','height': '600px'},config={"displayModeBar": False}),#
                        xs=12, sm=12, md=12, lg=12, xl=12),
                ],className="g-0" , style={'margin': '0', 'padding': '0'}),  # close Row config={'responsive': True},

                dcc.Download(id="download-pdf"),
                ]),

                id="collapse-plots",
                is_open=False
            )
    return charts

def add_pile_schedule_table():
    # DRILLED	NOT DRILLED	HOLD / NOT RELEASED	DELETED	ABANDONED	TOTAL
    columnDefs = [
        {"headerName": "Pile Type", "field": "PileType", "filter": True, "enableRowGroup": True},
        {"headerName": "DRILLED", "field": "JobName", "filter": True, "enableRowGroup": True},
        {"headerName": "NOT DRILLED", "field": "JobName", "filter": True, "enableRowGroup": True},
        {"headerName": "HOLD", "field": "JobName", "filter": True, "enableRowGroup": True},
        {"headerName": "DELETED", "field": "JobName", "filter": True, "enableRowGroup": True},
        {"headerName": "ABANDONED", "field": "JobName", "filter": True, "enableRowGroup": True},
        {"headerName": "TOTAL", "field": "JobName", "filter": True, "enableRowGroup": True},
    ]
    table = html.Div([
        html.H4("Pile Schedule", style={'color':'white','textAlign': 'left', 'marginBottom': 30}),
        # AG Grid
        dag.AgGrid(
            id="plie_schedule_table",
            columnDefs=columnDefs,
            rowData=[],
            className="ag-theme-alpine-dark",
            columnSize="sizeToFit",
            defaultColDef={
                "resizable": True,
                "sortable": True,
                "filter": True,
                "minWidth": 100,
                "wrapHeaderText": True,  # ✅ allow text wrapping in header
                "autoHeaderHeight": True,  # ✅ auto-adjust header height
            },

            dashGridOptions={
                "rowSelection": "single",
                "pagination": True,
                "paginationPageSize": 20,
                "enableRangeSelection": True,
                "enableCharts": True,
                "animateRows": False,
                "enableSorting": True,
                "enableFilter": True,
                "enableRangeHandle": True,

            },

            style={"height": "600px", "width": "100%", "marginTop": '5px'}
        ),

    ])

    return table


# ======================================================================================
# =============JOB METRICS==============================================================
# ======================================================================================
# JobNo	Time	RigID	Production Piles	Pile Count	ConcreteDelivered	LaborHours	RigDays	DaysRigDrilled	AveragePileLength	AveragePileWaste	AverageRigWaste
# def add_drilling_summary():
#     #  {"headerName": "Field", "field": "Field",
#     columnDefs = [
#         {"headerName": "JobNo", "field": "JobNo", "filter": True, "enableRowGroup": True},
#         {"headerName": "Job\nName","field": "JobName", "filter": True, "enableRowGroup": True},
#         {"headerName": "Date","field": "Date", "filter": True, "enableRowGroup": True},
#         {"field": "RigID", "filter": True, "enableRowGroup": True},
#         {"headerName": "Piles\nTotal", "field": "PileCount", "filter": "agNumberColumnFilter"},
#         {"headerName": "Concrete\nDelivered", "field": "ConcreteDelivered", "filter": "agNumberColumnFilter"},
#         {"headerName": "Labor\nHours", "field": "LaborHours", "filter": "agNumberColumnFilter"},
#         {"headerName": "Days Rig\nDrilled", "field": "DaysRigDrilled", "filter": "agNumberColumnFilter"},
#         {"headerName": "Avg\nPile Length", "field": "AveragePileLength", "filter": "agNumberColumnFilter"},
#         {"headerName": "Avg\nPile Waste", "field": "AveragePileWaste", "filter": "agNumberColumnFilter"},
#         {"headerName": "Avg\nRig Waste", "field": "AverageRigWaste", "filter": "agNumberColumnFilter"},
#     ]
#     return html.Div([
#         html.H4("Drilling Summary (!Work in Progress!)", style={'color':'white','textAlign': 'left', 'marginBottom': 30}),
#
#         # Controls Row
#         html.Div([
#             # Grouping Controls
#             html.Div([
#                 html.Label("Select Grouping Level:", style={'color':'white','fontWeight': 'bold'}),
#                 dcc.Dropdown(
#                     id='grouping-level',
#                     options=[
#                         {'label': 'Overall', 'value': 'overall'},
#                         {'label': 'Job Daily Level', 'value': 'daily'},
#                         {'label': 'Job Total Level', 'value': 'jobno'},
#                         {'label': 'RigID Total Level', 'value': 'rigid'},
#                         {'label': 'No Grouping (Raw Data)', 'value': 'none'}
#                     ],
#                     value='jobno',
#                     style={'width': '100%'},
#                     className="dark-dropdown"
#                 )
#             ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px'}),
#
#             # # Date Range Controls
#             # html.Div([
#             #     html.Label("Date Range Filter:", style={'fontWeight': 'bold'}),
#             #     dcc.DatePickerRange(
#             #         id='date-range',
#             #         start_date=min_date,
#             #         end_date=max_date,
#             #         min_date_allowed=min_date,
#             #         max_date_allowed=max_date,
#             #         display_format='YYYY-MM-DD',
#             #         style={'width': '100%'}
#             #     )
#             # ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
#
#             # Export Controls
#             # html.Div([
#             #     # html.Label("Export Rig Summary Data:", style={'fontWeight': 'bold'}),
#             #     # html.Br(),
#             #     html.Button("Export Summary to CSV", id="btn-rigsummary-export-csv", n_clicks=0,
#             #                 style={'backgroundColor': '#0074D9', 'color': 'white',
#             #                        'border': 'none', 'padding': '8px 16px',
#             #                        'borderRadius': '4px', 'cursor': 'pointer',"align":'left'}),
#             #     dcc.Download(id="download-dataframe-csv")
#             # ], style={'width': '23%', 'display': 'inline-block', 'padding': '10px', 'verticalAlign': 'top'}),
#
#             # Info Display
#             # html.Div([
#             #     html.Label("Current View:", style={'fontWeight': 'bold'}),
#             #     html.Div(id='grid-info', style={'marginTop': '5px', 'fontSize': '14px'})
#             # ], style={'width': '20%', 'display': 'inline-block', 'padding': '10px', 'verticalAlign': 'top'})
#         ], style={ 'marginBottom': '20px', 'padding': '10px'}),#'border': '1px solid #ddd', 'borderRadius': '5px',
#
#         # AG Grid
#         dag.AgGrid(
#             id="rig-summary-data-grid",
#             columnDefs=columnDefs,
#             rowData=[],
#             className="ag-theme-alpine-dark",
#             columnSize="sizeToFit",
#             defaultColDef= {
#             "resizable": True,
#             "sortable": True,
#             "filter": True,
#             "minWidth": 100,
#             "wrapHeaderText": True,  # ✅ allow text wrapping in header
#             "autoHeaderHeight": True,  # ✅ auto-adjust header height
#             },
#
#             dashGridOptions={
#                 "rowSelection": "single",
#                 "pagination": True,
#                 "paginationPageSize": 20,
#                 "enableRangeSelection": True,
#                 "enableCharts": True,
#                 "animateRows": False,
#                 "enableSorting": True,
#                 "enableFilter": True,
#                 "enableRangeHandle": True,
#
#             },
#
#             style={"height": "600px", "width": "100%","marginTop":'5px'}
#         ),
#
#     ])

def add_drilling_summary():
    columnDefs = [
        {"headerName": "JobNo", "field": "JobNo", "filter": True, "enableRowGroup": True},
        {"headerName": "Job\nName", "field": "JobName", "filter": True, "enableRowGroup": True},
        {"headerName": "Date", "field": "Date", "filter": True, "enableRowGroup": True},
        {"field": "RigID", "filter": True, "enableRowGroup": True},
        {"headerName": "Piles\nTotal", "field": "PileCount", "filter": "agNumberColumnFilter"},
        {"headerName": "Concrete\nDelivered", "field": "ConcreteDelivered", "filter": "agNumberColumnFilter"},
        {"headerName": "Labor\nHours", "field": "LaborHours", "filter": "agNumberColumnFilter"},
        {"headerName": "Days Rig\nDrilled", "field": "DaysRigDrilled", "filter": "agNumberColumnFilter"},
        {"headerName": "Avg\nPile Length", "field": "AveragePileLength", "filter": "agNumberColumnFilter"},
        {"headerName": "Avg\nPile Waste", "field": "AveragePileWaste", "filter": "agNumberColumnFilter"},
        {"headerName": "Avg\nRig Waste", "field": "AverageRigWaste", "filter": "agNumberColumnFilter"},
    ]

    return html.Div([
        html.H4("Drilling Summary (!Work in Progress!)",
                style={'color': 'white', 'textAlign': 'left', 'marginBottom': 30}),

        # Controls Row
        html.Div([
            # Grouping Buttons
            html.Div([
                html.Label("Select Grouping Level:",
                           style={'color': 'white', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                html.Div([
                    html.Button("Overall", id="btn-overall", n_clicks=0,
                                className="grouping-button active",
                                style={'marginRight': '5px', 'marginBottom': '5px'}),
                    html.Button("By Job", id="btn-daily", n_clicks=0,
                                className="grouping-button",
                                style={'marginRight': '5px', 'marginBottom': '5px'}),
                    # html.Button("Job Total", id="btn-jobno", n_clicks=0,
                    #             className="grouping-button active",
                    #             style={'marginRight': '5px', 'marginBottom': '5px'}),
                    html.Button("By Rig", id="btn-rigid", n_clicks=0,
                                className="grouping-button",
                                style={'marginRight': '5px', 'marginBottom': '5px'}),
                    html.Button("Raw Data", id="btn-none", n_clicks=0,
                                className="grouping-button",
                                style={'marginBottom': '5px'}),
                ], style={'display': 'flex', 'flexWrap': 'wrap'}),
            ], style={'width': '60%', 'display': 'inline-block', 'padding': '10px', 'verticalAlign': 'top'}),

            # Cumulative/Daily Switch
            html.Div([
                html.Label("Data View:", style={'color': 'white', 'fontWeight': 'bold', 'marginBottom': '10px'}),
                html.Div([
                    html.Span("Daily", style={'color': 'white', 'marginRight': '10px', 'fontSize': '14px'}),
                    daq.BooleanSwitch(
                        id='cumulative-switch',
                        on=True,
                        color="#007BFF",
                        style={'display': 'inline-block'}
                    ),
                    html.Span("Cumulative", style={'color': 'white', 'marginLeft': '10px', 'fontSize': '14px'}),
                ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'})
            ], style={'width': '35%', 'display': 'inline-block', 'padding': '10px', 'textAlign': 'center',
                      'verticalAlign': 'top'}),

        ], style={'marginBottom': '20px', 'padding': '10px'}),

        # AG Grid
        dag.AgGrid(
            id="rig-summary-data-grid",
            columnDefs=[],
            rowData=[],
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
                "paginationPageSize": 20,
                "enableRangeSelection": True,
                "enableCharts": True,
                "animateRows": False,
                "enableSorting": True,
                "enableFilter": True,
                "enableRangeHandle": True,
            },
            style={"height": "600px", "width": "100%", "marginTop": '5px'}
        ),
        html.Button(
            "Download CSV",
            id="btn-download-csv",
            n_clicks=0,
            className="grouping-button",
            style={'marginTop': '5px'}
        ),
        dcc.Download(id="download-dataframe-csv"),

    ])


# charts_details = {'cone':['Cone Resistence (tsf) ',['q_c (tsf)','q_t (tsf)']],
#                   'friction':['Friction Ratio %',['R_f (%)']],
#                   'pore':["Pore Pressure (ft-head)",['U_2 (ft-head)','U_0 (ft-head)']],
#                   'sbt':["Soil Behaviour Type",['Zone_Icn']],
#                   'norm_cone':["Normalized Cone Resistance",['Q_t','Q_tn']],
#                   "sbi":["Soil Behavior Index",['Ic']],
#                   "sleve":["Sleeve Friction (tsf)",['f_s (tsf)']],
#                   "bq":["Pore Pressure Parameter",['B_q']],
#                   "capacity":['Capacity (Tons)',['Q_s (Tons)','Q_b (Tons)','Q_ult (Tons)']]
#                   }
# def add_chart_controls():
#     layout = html.Div([
#         # Collapse toggle
#         dbc.Button("View Chart Controls", id="toggle-controls-mwd", className="mb-2", color="secondary"),
#         dbc.Collapse([
#             # html.H4("CPT Chart Controls", style={"color": "white"}),
#             # Template dropdown
#             html.Div([
#                 html.Label("Layout Template:", style={"color": "white"}),
#                 dcc.Dropdown(
#                     id="template-selector-mwd",
#                     options=[
#                         {"label": "Landscape (4 charts)", "value": "4"},
#                         {"label": "Portrait (3 charts)", "value": "3"},
#                     ],
#                     value="landscape",
#                     clearable=False,
#                     className="dark-dropdown"
#                 )
#             ], style={"width": "300px", "margin-bottom": "20px"}),
#
#             # Chart type selection
#             html.Div([
#                 html.Label("Select Chart Types:", style={"color": "white"}),
#                 dcc.Dropdown(
#                     id="chart-type-selector-mwd",
#                     options=[{"label": v[0], "value": k} for k, v in charts_details.items()],
#                     multi=True,
#                     value=["cone", "friction", "pore", "sbt"],
#                     className="dark-dropdown"
#                 )
#             ], style={"width": "100%", "margin-bottom": "20px"}),
#
#             # Y-axis dropdown + min/max input
#             html.Div([
#                 html.Label("Y-Axis Scale and Range:", style={"color": "white"}),
#                 dbc.Row([
#                     dbc.Col(
#                         dcc.Dropdown(
#                             id="y-axis-mode-mwd",
#                             options=[
#                                 {"label": "Elevation (feet)", "value": "elevation"},
#                                 {"label": "Depth (feet)", "value": "depth"}
#                             ],
#                             value="elevation",
#                             clearable=False,
#                             className="dark-dropdown"
#                         ),
#                         width=4
#                     ),
#                     dbc.Col(
#                         dbc.Input(id="y-axis-min-mwd", type="number", placeholder="Min",
#                                   style={"background": "#193153", "color": "white"}),
#                         width=2
#                     ),
#                     dbc.Col(
#                         dbc.Input(id="y-axis-max-mwd", type="number", placeholder="Max",
#                                   style={"background": "#193153", "color": "white"}),
#                         width=2
#                     )
#                 ])
#             ], style={"margin-bottom": "30px"}),
#
#             # Inputs for x-axis ranges
#             html.Div([
#                 html.Label("X-Axis Ranges (Min/Max):", style={"color": "white"}),
#                 dbc.Row([
#                     dbc.Col([
#                         html.Div(id="chart1-label-mwd", children=html.Label("Chart #1", style={"color": "white"})),
#                         dbc.InputGroup([
#                             dbc.InputGroupText("Min", style={"background": "#102640", "color": "white"}),
#                             dbc.Input(id="x1-min-mwd", type="number", style={"background": "#193153", "color": "white"})
#                         ], className="mb-4"),
#                         dbc.InputGroup([
#                             dbc.InputGroupText("Max", style={"background": "#102640", "color": "white"}),
#                             dbc.Input(id="x1-max-mwd", type="number", style={"background": "#193153", "color": "white"})
#                         ])
#                     ]),
#                     dbc.Col([
#                         html.Div(id="chart2-label-mwd", children=html.Label("Chart #2", style={"color": "white"})),
#                         dbc.InputGroup([
#                             dbc.InputGroupText("Min", style={"background": "#102640", "color": "white"}),
#                             dbc.Input(id="x2-min-mwd", type="number", style={"background": "#193153", "color": "white"})
#                         ], className="mb-4"),
#                         dbc.InputGroup([
#                             dbc.InputGroupText("Max", style={"background": "#102640", "color": "white"}),
#                             dbc.Input(id="x2-max-mwd", type="number", style={"background": "#193153", "color": "white"})
#                         ])
#                     ]),
#                     dbc.Col([
#                         html.Div(id="chart3-label-mwd", children=html.Label("Chart #3", style={"color": "white"})),
#                         dbc.InputGroup([
#                             dbc.InputGroupText("Min", style={"background": "#102640", "color": "white"}),
#                             dbc.Input(id="x3-min-mwd", type="number", style={"background": "#193153", "color": "white"})
#                         ], className="mb-4"),
#                         dbc.InputGroup([
#                             dbc.InputGroupText("Max", style={"background": "#102640", "color": "white"}),
#                             dbc.Input(id="x3-max-mwd", type="number", style={"background": "#193153", "color": "white"})
#                         ])
#                     ]),
#                     dbc.Col([
#                         html.Div(id="chart4-label-mwd", children=html.Label("None", style={"color": "white"})),
#                         dbc.InputGroup([
#                             dbc.InputGroupText("Min", style={"background": "#102640", "color": "white"}),
#                             dbc.Input(id="x4-min-mwd", type="number", style={"background": "#193153", "color": "white"})
#                         ], className="mb-4"),
#                         dbc.InputGroup([
#                             dbc.InputGroupText("Max", style={"background": "#102640", "color": "white"}),
#                             dbc.Input(id="x4-max-mwd", type="number", style={"background": "#193153", "color": "white"})
#                         ])
#                     ]),
#                 ], className="mb-4")
#             ]),
#
#
#             # =============================================
#             html.Hr(style={"borderTop": "1px solid white"}),
#
#
#             html.Div([
#                 # Save section
#                 html.Label("Save Settings As:", style={"color": "white"}),
#                 dbc.Input(
#                     id="profile-name-mwd",
#                     placeholder="e.g. default, run1, clientXYZ",
#                     type="text",
#                     style={"background": "#193153", "color": "white", "marginBottom": "10px"}
#                 ),
#
#                 # Load section
#                 html.Label("Load Saved Settings (please select JobID and CPTID):", style={"color": "white"}),
#                 dcc.Dropdown(
#                     id="load-settings-dropdown-mwd",
#                     options=[],
#                     className="dark-dropdown",
#                     style={"marginBottom": "10px"}
#                 ),
#
#                 # Buttons in a row
#                 dbc.Row([
#                     dbc.Col(dbc.Button("💾 Save Settings", id="save-settings-btn", color="info", className="w-100"),
#                             width="auto"),
#                     dbc.Col(dbc.Button("📂 Load Settings", id="load-settings-btn", color="success", className="w-100"),
#                             width="auto"),
#                     dbc.Col(dbc.Button("⟳ Reset Controls", id="reset-controls-btn", color="warning", className="w-100"),
#                             width="auto"),
#                 ], justify="start", className="g-2")  # g-2 adds gutter spacing
#             ], style={"width": "100%", "marginTop": "20px"}),
#
#             dcc.Store(id="chart-settings-mwd"),
#             # =============================================
#             html.Br(),
#             dbc.Button("Update Chart", id="update-btn", color="primary", className="mb-2"),
#
#         ],
#             id="chart-controls-collapse-mwd",
#             is_open=False
#         )
#     ])
#
#     return layout


