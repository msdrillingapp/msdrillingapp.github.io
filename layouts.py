from dash import dcc
from dash import html
from datetime import datetime as dt
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

   pileList = html.Div([
        # Map Section
        dbc.Button("Show Pile List", id="toggle-pilelist", color="primary", className="mb-2"),
        dbc.Collapse(
            [
                dag.AgGrid(
                    id="pilelist-table",
                    columnDefs=[
                        {"headerName": "PileID", "field": "PileID", "sortable": True, "filter": True, "pinned": "left"},
                        {"headerName": "Time", "field": "Time", "sortable": True, "filter": True},
                        {"headerName": "JobID", "field": "JobID", "sortable": True, "filter": True, "hide": True},
                        {"headerName": "LocationID", "field": "LocationID", "sortable": True, "filter": True,"headerClass": "header-red" },
                        {"headerName": "MinDepth", "field": "MinDepth", "sortable": True, "filter": True,"editable": True,"headerClass": "header-red"},
                        {"headerName": "MaxStrokes", "field": "MaxStrokes", "sortable": True, "filter": True, "editable": True,"headerClass": "header-red"},
                        {"headerName": "OverBreak", "field": "OverBreak", "sortable": True, "filter": True,"editable": False},
                        {"headerName": "PileStatus", "field": "PileStatus", "sortable": True, "filter": True, "editable": True,"cellEditor": "agSelectCellEditor",
                        "cellEditorParams": {"values": ["Complete", "Abandoned"]},"headerClass": "header-red"},
                        {"headerName": "PileCode", "field": "PileCode", "sortable": True, "filter": True,"editable": True, "cellEditor": "agSelectCellEditor",
                         "cellEditorParams": {"values": ["Production Pile", "Test Pile","Recation Pile","Probe"]},"headerClass": "header-red" },
                        {"headerName": "Comments", "field": "Comments", "sortable": True, "filter": True, "editable": True,"headerClass": "header-red"},
                        {"headerName": "DelayTime", "field": "DelayTime", "sortable": True, "filter": True, "editable": False},
                        {"headerName": "Delay", "field": "Delay", "sortable": True, "filter": True, "editable": True,
                         "cellEditor": "agSelectCellEditor", "cellEditorParams": {"values": ['Waiting on Concrete', 'Site access', 'Layout','Other']},"headerClass": "header-red"},
                         {"headerName": "PumpID", "field": "PumpID", "sortable": True, "filter": True, "editable": True,"headerClass": "header-red"},
                        {"headerName": "Calibration", "field": "Calibration", "sortable": True, "filter": True, "editable": True,"headerClass": "header-red"},
                        {"headerName": "PileType", "field": "PileType", "sortable": True, "filter": True, "editable": False,
                            "cellEditor": "agSelectCellEditor", "cellEditorParams": {"values": ["1", "2", "3", "3A", "4", "5"]},},
                        {"headerName": "Distance", "field": "Distance", "sortable": True, "filter": True, "editable": False},
                        {"headerName": "MoveTime", "field": "MoveTime", "sortable": True, "filter": True, "editable": False},
                        {"headerName": "Totaltime", "field": "Totaltime", "sortable": True, "filter": True, "editable": False},

                        {"headerName": "RigID", "field": "RigID", "sortable": True, "filter": True, "hide": True},
                        {"headerName": "Client", "field": "Client", "sortable": True, "filter": True, "hide": True},
                        {"headerName": "DrillStartTime", "field": "DrillStartTime", "sortable": True, "filter": True, "hide": True},
                        {"headerName": "DrillEndTime", "field": "DrillEndTime", "sortable": True, "filter": True, "hide": True},
                        {"headerName": "PileLength", "field": "PileLength", "sortable": True, "filter": True,"hide": True},
                        {"headerName": "PileDiameter", "field": "PileDiameter", "sortable": True, "filter": True, "hide": True},

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
                html.Button("Download PDF for ALL PileID", id='download-ALL-pdf-btn', disabled=False,style={'marginLeft': '5px'}),
                # ,style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between','marginLeft': '5px'}
                html.Button("Save changes", id="btn_save", n_clicks=0,style={'marginLeft': '5px'}),
                dcc.Download(id="download-csv"),

                # dcc.Interval(id="check-task-interval", interval=2000, n_intervals=0, disabled=True),

                dcc.Download(id="download-ALL-pdf"),
                dcc.Interval(id="poll-interval", interval=1000, n_intervals=0, disabled=True),
                dcc.Store(id="task-id"),
                html.Div(id="task-status"),

                # html.A("Download ZIP", id="download-link", href="", style={'display': 'none'})
                # html.Div(id="download-link-container", children=[]),
                # html.Div(id="task-status"),
                # html.Div(id="task-output", className="mt-3"),


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

def add_charts():
    charts =  dbc.Collapse(
            html.Div([
                # Statistics Info Cards
                html.Div(id="pile-summary-cards", style={
                    'display': 'flex', 'justifyContent': 'space-around', 'alignItems': 'center',
                    'backgroundColor': '#193153', 'color': 'white', 'padding': '10px',
                    'borderRadius': '5px', 'marginTop': '10px'
                }),

                html.Button("Download PDF for PileID", id='download-pdf-btn', disabled=True),
                dbc.Row([
                    dbc.Col(
                            dcc.Graph(id="time_graph", style={"backgroundColor": "#193153",'width': '100%','marginBottom':'5px'}),
                    xs=12, sm=12, md=12, lg=12, xl=12),
                    ]), # close Row config={'responsive': True},
                # html.Div([
                dbc.Row([
                    dbc.Col(
                        dcc.Graph(id="depth_graph", style={"backgroundColor": "#193153",'marginTop':'5px'}),
                        xs=12, sm=12, md=12, lg=12, xl=12),
                ]),  # close Row config={'responsive': True},

                dcc.Download(id="download-pdf"),
                ]),

                id="collapse-plots",
                is_open=False
            )
    return charts
