import dash
from dash import dcc, html, Output, Input, State, ClientsideFunction, callback,no_update,ctx
from functions import cpt_header,jobid_cpt_data
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import os
import base64
from io import BytesIO
import plotly.io as pio
import json
from datetime import datetime
#---------------------------------------------------------------
from report_template import PileReportHeader
#---------------------------------------------------------------
columns_cpt = ['Depth (feet)','Elevation (feet)','q_c (tsf)','q_t (tsf)','f_s (tsf)','U_2 (ft-head)','U_0 (ft-head)','R_f (%)','Zone_Icn','SBT_Icn','B_q','F_r','Q_t','Ic','Q_tn','Q_s (Tons)','Q_b (Tons)','Q_ult (Tons)']
zone_colors = {
    1: "#fcacc1",   # Sensitive Soils
    2: "#fcd4e5",   # Organic Soils
    3: "#5f6bd6",   # Clays
    4: "#70b1b0",   # Silty Mix
    5: "#b3db7e",   # Sandy Mix
    6: "#f47e43",   # Sands
    7: "#e5c36e",   # Gravelly Sands
    8: "#dcd7c2",   # Stiff Clayey Sands
    9: "#c78cc9",   # Very Stiff Clays and Silts
    0: 'black'
}


charts_details = {'cone':['Cone Resistence (tsf) ',['q_c (tsf)','q_t (tsf)']],
                  'friction':['Friction Ratio %',['R_f (%)']],
                  'pore':["Pore Pressure (ft-head)",['U_2 (ft-head)','U_0 (ft-head)']],
                  'sbt':["Soil Behaviour Type",['Zone_Icn']],
                  'norm_cone':["Normalized Cone Resistance",['Q_t','Q_tn']],
                  "sbi":["Soil Behavior Index",['Ic']],
                  "sleve":["Sleeve Friction (tsf)",['f_s (tsf)']],
                  "bq":["Pore Pressure Parameter",['B_q']],
                  "capacity":['Capacity (Tons)',['Q_s (Tons)','Q_b (Tons)','Q_ult (Tons)']]
                  }

dash.register_page(
    __name__,
    path_template="/CPT",
    path="/CPT",
)

logo_path = os.path.join(os.getcwd(), "assets","MSB.logo.JPG" )

SETTINGS_DIR = "chart_profiles"
os.makedirs(SETTINGS_DIR, exist_ok=True)

# =================================================================
# ========== FUNCTIONS =============================================
# =================================================================

# Helper function to find closest x value and create annotation
def get_closest_x(y_series, x_series, target_y):
    idx = (y_series - target_y).abs().idxmin()
    return x_series.iloc[idx]#, idx
def get_filters_cpt(cpt_header):
    cpt_header = cpt_header.copy()
    filters = html.Div([
        dbc.Row([
            dbc.Col(
                dcc.Dropdown(
                id="jobid-filter-cpt",
                options=[{"label": str(r), "value": str(r)} for r in cpt_header],
                placeholder="Filter by JobID",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            )),

            dbc.Col(dcc.Dropdown(
                id="pileid-filter-cpt",
                options=[],
                placeholder="Filter by CPTID",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            ))
        ]),
    ], style={'marginBottom': '10px', 'display': 'flex', 'justifyContent': 'center'})
    return filters


def add_subchart(fig,pile_info,y_ax, selected_charts):
    colors = ['red','blue','green']
    for i,chart in enumerate(selected_charts):
        pos = i + 1
        variables = charts_details[chart][1]
        legend = [x.split('(')[0] for x in variables]
        if chart!='sbt':
            for j,v in enumerate(variables):
                c = colors[j]
                # Add traces
                fig.add_trace(
                    go.Scatter(x=pile_info[v], y=y_ax, mode='lines', line=dict(color=c, width=2), name=v+"<br>",
                               showlegend=True),
                    row=1, col=pos
                )

            annotation_text = "<br>".join([
                f"<span style='color:{colors[j]}'>{v}</span>"
                for j, v in enumerate(legend)
            ])

            x_ann = max(pile_info[variables[0]]) #- 0.05*max(pile_info[variables[0]])
            fig.add_annotation(
                xref="x1", yref="paper",
                x=x_ann, y=-5,
                text=annotation_text,
                showarrow=False,
                align='right',
                font=dict(size=11),
                bgcolor="rgba(0,0,0,0)",
                row=1, col=pos
            )
            # fig.update_xaxes(title_text="tsf", row=1, col=pos)
        else:
            zones = pile_info['Zone_Icn']
            zones = list(np.nan_to_num(zones))
            colors_zone = [zone_colors[i] for i in zones]
            fig.add_trace(
                go.Bar(
                    x=pile_info['Zone_Icn'],
                    y=y_ax,
                    orientation='h',
                    marker=dict(color=colors_zone, line=dict(color='rgba(0,0,0,0)', width=0)),
                    showlegend=False,
                    hoverinfo='text',
                    hovertext=pile_info['SBT_Icn'],
                    base=0,  # This ensures bars start at 0
                ),
                row=1, col=pos
            )
            fig.update_xaxes(title_text="SBT (Robertson, 2010)", row=1, col=pos)
    return fig
def create_cpt_charts(pile_info, use_depth: bool = False, y_value: float = None, num_charts:int=4, selected_charts=None):
    pile_info = pile_info.copy()  # Prevent dataframe mutation
    if use_depth:
        y_ax_name = 'Depth (feet)'
    else:
        y_ax_name = 'Elevation (feet)'

    minD = min(pile_info[y_ax_name]) - 5
    maxD = max(pile_info[y_ax_name]) + 5
    subtitles = [charts_details[v][0] for v in selected_charts]

    fig = make_subplots(
        rows=1,
        cols=num_charts,
        shared_yaxes=True,
        subplot_titles=subtitles,
        horizontal_spacing=0.05
    )
    # Move subplot titles higher by modifying the annotations
    for annotation in fig['layout']['annotations']:
        annotation['y'] += 0.05  # Adjust this value as needed

    y_ax = pile_info[y_ax_name]

    fig = add_subchart(fig, pile_info, y_ax, selected_charts)


    # # Add horizontal line and value annotations if y_value is provided
    # if y_value is not None:
    #     filtered_data = {k: pile_info[k] for k in columns_cpt if k in pile_info}
    #     # Find the closest data point to the selected y_value for each trace
    #     df = pd.DataFrame(filtered_data)
    #     # Add horizontal line to each subplot
    #     for col in range(1, 5):
    #         fig.add_hline(
    #             y=y_value,
    #             line_dash="dot",
    #             line_color="cyan",
    #             line_width=2,
    #             row=1, col=col
    #         )
    #         # Add value annotations for each trace in the subplot
    #         if col == 1:  # Cone resistance (q_c and q_t)
    #             qc_x = get_closest_x(df[y_ax_name], df['q_c (tsf)'], y_value)
    #             qt_x = get_closest_x(df[y_ax_name], df['q_t (tsf)'], y_value)
    #
    #             fig.add_annotation(
    #                 x=qc_x, y=y_value,
    #                 text=f"q_c: {qc_x:.2f}",
    #                 showarrow=True,
    #                 arrowhead=1,
    #                 ax=20,
    #                 ay=10,
    #                 bgcolor="rgba(255,0,0,0.7)",
    #                 row=1, col=1
    #             )
    #             fig.add_annotation(
    #                 x=qt_x, y=y_value,
    #                 text=f"q_t: {qt_x:.2f}",
    #                 showarrow=True,
    #                 arrowhead=1,
    #                 ax=20,
    #                 ay=-10,
    #                 bgcolor="rgba(0,0,255,0.7)",
    #                 row=1, col=1
    #             )
    #
    #         elif col == 2:  # Friction Ratio (R_f)
    #             rf_x = get_closest_x(df[y_ax_name], df['R_f (%)'], y_value)
    #             fig.add_annotation(
    #                 x=rf_x, y=y_value,
    #                 text=f"R_f: {rf_x:.2f}%",
    #                 showarrow=True,
    #                 arrowhead=1,
    #                 ax=0,
    #                 ay=10,
    #                 bgcolor="rgba(255,0,0,0.7)",
    #                 row=1, col=2
    #             )
    #
    #         elif col == 3:  # Pore Pressure (U_2 and U_0)
    #             u2_x = get_closest_x(df[y_ax_name], df['U_2 (ft-head)'], y_value)
    #             u0_x = get_closest_x(df[y_ax_name], df['U_0 (ft-head)'], y_value)
    #
    #             fig.add_annotation(
    #                 x=u2_x, y=y_value,
    #                 text=f"U_2: {u2_x:.2f}",
    #                 showarrow=True,
    #                 arrowhead=1,
    #                 ax=0,
    #                 ay=10,
    #                 bgcolor="rgba(255,0,0,0.7)",
    #                 row=1, col=3
    #             )
    #             fig.add_annotation(
    #                 x=u0_x, y=y_value,
    #                 text=f"U_0: {u0_x:.2f}",
    #                 showarrow=True,
    #                 arrowhead=1,
    #                 ax=0,
    #                 ay=-10,
    #                 bgcolor="rgba(0,0,255,0.7)",
    #                 row=1, col=3
    #             )

    # Update layout
    fig.update_layout(
        yaxis_title=y_ax_name,
        plot_bgcolor="#193153",
        paper_bgcolor="#193153",
        font=dict(color="white"),
        showlegend=False,
        dragmode="select",
        autosize=True,
        margin=dict(l=50, r=50, b=50, t=50, pad=4)
    )


    # Configure gridlines for each subplot
    for i in range(1, num_charts+1):
        fig.update_xaxes(
            zerolinecolor='black',
            gridcolor='rgba(100,100,100,0.5)',
            gridwidth=1,
            showgrid=True,
            linecolor='black',
            mirror=True,
            minor=dict(showgrid=True, gridcolor='rgba(100,100,100,0.5)', griddash='dot'),
            row=1,
            col=i
        )
        fig.update_yaxes(
            zerolinecolor='black',
            gridcolor='rgba(100,100,100,0.5)',
            gridwidth=1,
            showgrid=True,
            linecolor='black',
            mirror=True,
            minor=dict(showgrid=True, gridcolor='rgba(100,100,100,0.5)', griddash='dot'),
            row=1,
            col=i
        )

    fig.update_annotations(font_size=11)
    fig.update_yaxes(range=[maxD, minD])

    fig.update_layout(autosize=False, height=600)
    fig = go.Figure(fig)  # Create fresh figure object
    return fig


def add_cpt_charts():
    charts = dbc.Collapse(
        html.Div([
            html.Button("Download PDF for PileID", id='download-pdf-btn-cpt', disabled=True),
            dbc.Row([
                dbc.Col(
                    dcc.Graph(
                        id="cpt_graph",
                        style={"backgroundColor": "#193153", 'width': '100%', 'marginBottom': '5px','height': '500px'},
                        config={'displayModeBar': False}
                    ),
                    xs=12, sm=12, md=12, lg=12, xl=12
                ),
            ]),
            dcc.Download(id="download-pdf-cpt"),
            # Add the slider below the graph
            # dbc.Row([
            #     dbc.Col(
            #         dcc.Slider(
            #             id='y-value-slider',
            #             min=0,
            #             max=100,
            #             value=50,
            #             step=0.1,
            #             marks=None,
            #             tooltip={"placement": "bottom", "always_visible": True},
            #             className="custom-slider"
            #         ),
            #         width=12
            #     )
            # ], style={'marginTop': '20px', 'padding': '0 20px'}),
            # # Store the current y-value
            # dcc.Store(id='current-y-value', storage_type='memory', data=None)

        ]),
        id="collapse-plots-cpt",
        is_open=False
    )
    return charts

def add_chart_controls():
    layout = html.Div([
        # Collapse toggle
        dbc.Button("View Chart Controls", id="toggle-controls-btn", className="mb-2", color="secondary"),
        dbc.Collapse([
            # html.H4("CPT Chart Controls", style={"color": "white"}),
            # Template dropdown
            html.Div([
                html.Label("Layout Template:", style={"color": "white"}),
                dcc.Dropdown(
                    id="template-selector",
                    options=[
                        {"label": "Landscape (4 charts)", "value": "4"},
                        {"label": "Portrait (3 charts)", "value": "3"},
                    ],
                    value="landscape",
                    clearable=False,
                    className="dark-dropdown"
                )
            ], style={"width": "300px", "margin-bottom": "20px"}),

            # 1) U_0 and U_2 (Pore pressure)
            # 2) f_s Sleeve Friction
            # 3)R_f (Friction Ratio) and F_r  (Normalized Friction Ratio)
            # 4)q_c and q_t (Cone resistance)
            # 5)Q_t and Q_tn  Normalized Cone Resistance
            # 6)Ic, Icn Soil Behavior Index
            # 7)Zone_Icn, SBT_Icn  (Soil behaviourType) SBT#
            # 8) B_q  Pore Pressure Parameter
            # 9)Q_s,Q_b,Q_ult (Capacity)   Ultimate Pile Capacity , Shaft, Base, Total -

            # Chart type selection
            html.Div([
                html.Label("Select Chart Types:", style={"color": "white"}),
                dcc.Dropdown(
                    id="chart-type-selector",
                    options=[{"label": v[0], "value": k} for k, v in charts_details.items()],
                    multi=True,
                    value=["cone", "friction", "pore", "sbt"],
                    className="dark-dropdown"
                )
            ], style={"width": "100%", "margin-bottom": "20px"}),

            # Y-axis dropdown + min/max input
            html.Div([
                html.Label("Y-Axis Scale and Range:", style={"color": "white"}),
                dbc.Row([
                    dbc.Col(
                        dcc.Dropdown(
                            id="y-axis-mode",
                            options=[
                                {"label": "Elevation (feet)", "value": "elevation"},
                                {"label": "Depth (feet)", "value": "depth"}
                            ],
                            value="elevation",
                            clearable=False,
                            className="dark-dropdown"
                        ),
                        width=4
                    ),
                    dbc.Col(
                        dbc.Input(id="y-axis-min", type="number", placeholder="Min",
                                  style={"background": "#193153", "color": "white"}),
                        width=2
                    ),
                    dbc.Col(
                        dbc.Input(id="y-axis-max", type="number", placeholder="Max",
                                  style={"background": "#193153", "color": "white"}),
                        width=2
                    )
                ])
            ], style={"margin-bottom": "30px"}),

            # Inputs for x-axis ranges
            html.Div([
                html.Label("X-Axis Ranges (Min/Max):", style={"color": "white"}),
                dbc.Row([
                    dbc.Col([
                        html.Div(id="chart1-label", children=html.Label("Chart #1", style={"color": "white"})),
                        dbc.InputGroup([
                            dbc.InputGroupText("Min", style={"background": "#102640", "color": "white"}),
                            dbc.Input(id="x1-min", type="number", style={"background": "#193153", "color": "white"})
                        ], className="mb-4"),
                        dbc.InputGroup([
                            dbc.InputGroupText("Max", style={"background": "#102640", "color": "white"}),
                            dbc.Input(id="x1-max", type="number", style={"background": "#193153", "color": "white"})
                        ])
                    ]),
                    dbc.Col([
                        html.Div(id="chart2-label", children=html.Label("Chart #2", style={"color": "white"})),
                        dbc.InputGroup([
                            dbc.InputGroupText("Min", style={"background": "#102640", "color": "white"}),
                            dbc.Input(id="x2-min", type="number", style={"background": "#193153", "color": "white"})
                        ], className="mb-4"),
                        dbc.InputGroup([
                            dbc.InputGroupText("Max", style={"background": "#102640", "color": "white"}),
                            dbc.Input(id="x2-max", type="number", style={"background": "#193153", "color": "white"})
                        ])
                    ]),
                    dbc.Col([
                        html.Div(id="chart3-label", children=html.Label("Chart #3", style={"color": "white"})),
                        dbc.InputGroup([
                            dbc.InputGroupText("Min", style={"background": "#102640", "color": "white"}),
                            dbc.Input(id="x3-min", type="number", style={"background": "#193153", "color": "white"})
                        ], className="mb-4"),
                        dbc.InputGroup([
                            dbc.InputGroupText("Max", style={"background": "#102640", "color": "white"}),
                            dbc.Input(id="x3-max", type="number", style={"background": "#193153", "color": "white"})
                        ])
                    ]),
                    dbc.Col([
                        html.Div(id="chart4-label", children=html.Label("None", style={"color": "white"})),
                        dbc.InputGroup([
                            dbc.InputGroupText("Min", style={"background": "#102640", "color": "white"}),
                            dbc.Input(id="x4-min", type="number", style={"background": "#193153", "color": "white"})
                        ], className="mb-4"),
                        dbc.InputGroup([
                            dbc.InputGroupText("Max", style={"background": "#102640", "color": "white"}),
                            dbc.Input(id="x4-max", type="number", style={"background": "#193153", "color": "white"})
                        ])
                    ]),
                ], className="mb-4")
            ]),
            # dbc.Button("💾 Save Settings", id="save-settings-btn", color="info", className="me-2"),
            # dbc.Button("📂 Load Settings", id="load-settings-btn", color="success"),
            # dcc.Store(id="chart-settings"),

            # =============================================
            html.Hr(style={"borderTop": "1px solid white"}),

            # html.Div([
            #     html.Label("Save Settings As:", style={"color": "white"}),
            #     dbc.Input(id="profile-name", placeholder="e.g. default, run1, clientXYZ", type="text",
            #               style={"background": "#193153", "color": "white"}),
            #     dbc.Button("💾 Save Settings", id="save-settings-btn", color="info", className="mt-2"),
            # # ], style={"width": "300px"}),
            # #
            # # html.Div([
            #
            #     html.Label("Load Saved Settings (please select JobID and CPTID):", style={"color": "white", "marginTop": "20px"}),
            #     dcc.Dropdown(id="load-settings-dropdown", options=[], className="dark-dropdown"),
            #     dbc.Button("📂 Load Settings", id="load-settings-btn", color="success", className="mt-2"),
            #
            #     dbc.Button("Reset Controls", id="reset-controls-btn", color="warning", className="mb-2 ms-2"),
            # ], style={"width": "300px", "marginTop": "20px"}),
            html.Div([
                # Save section
                html.Label("Save Settings As:", style={"color": "white"}),
                dbc.Input(
                    id="profile-name",
                    placeholder="e.g. default, run1, clientXYZ",
                    type="text",
                    style={"background": "#193153", "color": "white", "marginBottom": "10px"}
                ),

                # Load section
                html.Label("Load Saved Settings (please select JobID and CPTID):", style={"color": "white"}),
                dcc.Dropdown(
                    id="load-settings-dropdown",
                    options=[],
                    className="dark-dropdown",
                    style={"marginBottom": "10px"}
                ),

                # Buttons in a row
                dbc.Row([
                    dbc.Col(dbc.Button("💾 Save Settings", id="save-settings-btn", color="info", className="w-100"),
                            width="auto"),
                    dbc.Col(dbc.Button("📂 Load Settings", id="load-settings-btn", color="success", className="w-100"),
                            width="auto"),
                    dbc.Col(dbc.Button("⟳ Reset Controls", id="reset-controls-btn", color="warning", className="w-100"),
                            width="auto"),
                ], justify="start", className="g-2")  # g-2 adds gutter spacing
            ], style={"width": "100%", "marginTop": "20px"}),

            dcc.Store(id="chart-settings"),
            # =============================================
            html.Br(),
            dbc.Button("Update Chart", id="update-btn", color="primary", className="mb-2"),

        ],
            id="chart-controls-collapse",
            is_open=False
        )
    ])

    return layout
# =================================================================
# =================================================================
# =================================================================
flts = get_filters_cpt(cpt_header)
charts = add_cpt_charts()
controls = add_chart_controls()

layout = html.Div([
    dcc.Store(id='window-size', data={'width': 1200}),
    html.Br(),
    flts,
    controls,
    dbc.Button("Show Plots", id="toggle-plots-cpt", color="primary", className="mb-2", style={"marginTop": "20px"}),
    charts
], style={'backgroundColor': '#193153', 'height': '550vh', 'padding': '20px', 'position': 'relative'})

#
# # Custom CSS for the slider
# app = dash.get_app()
# app.clientside_callback(
#     """
#     function(href) {
#         var style = document.createElement('style');
#         style.innerHTML = `
#             .custom-slider .rc-slider-track {
#                 background-color: #4a90e2;
#             }
#             .custom-slider .rc-slider-handle {
#                 border-color: #4a90e2;
#             }
#             .custom-slider .rc-slider-tooltip-inner {
#                 background-color: #4a90e2;
#                 color: white;
#             }
#         `;
#         document.head.appendChild(style);
#         return window.innerWidth;
#     }
#     """,
#     Output('window-size', 'data'),
#     Input('url', 'href')
# )


# =================================================================
# ========================CALLBACKS ===============================
# =================================================================
@callback(
    Output("cpt_graph", "figure"),
    Output('download-pdf-btn-cpt', 'disabled'),
    # Output('y-value-slider', 'min'),
    # Output('y-value-slider', 'max'),
    # Output('y-value-slider', 'value'),
    # Output('current-y-value', 'data'),
    Input("update-btn", "n_clicks"),
    Input('pileid-filter-cpt', 'value'),
    # Input('date-filter-cpt', 'value'),
    # Input('y-value-slider', 'value'),
    Input('cpt_graph', 'selectedData'),
    Input('window-size', 'data'),
    State("jobid-filter-cpt", "value"),
    # State('current-y-value', 'data'),
    State("y-axis-mode", "value"),
    State("x1-min", "value"), State("x1-max", "value"),
    State("x2-min", "value"), State("x2-max", "value"),
    State("x3-min", "value"), State("x3-max", "value"),
    State("x4-min", "value"), State("x4-max", "value"),
    State("y-axis-min", "value"),
    State("y-axis-max", "value"),
    State("chart-type-selector","value"),
    State("template-selector", "value"),
    prevent_initial_call=True
)#slider_value,current_y_value,
def update_cpt_graph(n_clicks,selected_pileid,  selected_data, window_size, selected_jobid,
                      y_mode, x1_min, x1_max, x2_min, x2_max, x3_min, x3_max, x4_min, x4_max,y_max,y_min,selected_charts,selected_template):

        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

        if not selected_pileid:
            return go.Figure(layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"}), True #, 0, 100, 50, None

        num_charts = 3 if selected_template=='3' else 4
        chart_types = selected_charts[:num_charts]

        use_depth = (y_mode == "depth")

        # Build a dict of x-axis limits
        x_limits = {
            1: (x1_min, x1_max),
            2: (x2_min, x2_max),
            3: (x3_min, x3_max),
            # 4: (x4_min, x4_max),
        }
        if num_charts == 4:
            x_limits[4] = (x4_min, x4_max)

        # Get pile data
        pile_info = jobid_cpt_data[selected_jobid]
        pile_info = pile_info[selected_pileid]
        # Determine y-axis range
        y_ax_name = 'Elevation (feet)'  # or 'Depth (feet)' based on your logic
        if y_min is None:
            minD = min(pile_info[y_ax_name]) - 5
        else:
            minD = y_min
        if y_max is None:
            maxD = max(pile_info[y_ax_name]) + 5
        else:
            maxD = y_max

        # Handle y-value updates
        # y_value = current_y_value if current_y_value is not None else (minD + maxD) / 2
        y_value = 0
        if trigger_id == 'y-value-slider':
            # y_value = slider_value
            y_value=0
            pass
        elif trigger_id == 'cpt_graph' and selected_data is not None:
            y_values = [point['y'] for point in selected_data['points']]
            if y_values:
                y_value = np.mean(y_values)

        # Create figure with current y-value and annotations
        fig = create_cpt_charts(pile_info,use_depth=use_depth, y_value=y_value,num_charts=num_charts,selected_charts=chart_types)

        # Apply x-axis ranges to each subplot
        for i in range(1, num_charts+1):
            min_val, max_val = x_limits[i]
            if min_val is not None and max_val is not None:
                fig.update_xaxes(range=[min_val, max_val], row=1, col=i)

        fig.update_yaxes(range=[maxD,minD])



        return fig, False #, minD, maxD, y_value,y_value



@callback(
    Output("collapse-plots-cpt", "is_open"),
    [Input("toggle-plots-cpt", "n_clicks")],
    [State("collapse-plots-cpt", "is_open")]
)
def toggle_plots(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open



# from plotly.subplots import make_subplots
@callback(
    Output("download-pdf-cpt", "data", allow_duplicate=True),
    Input("download-pdf-btn-cpt", "n_clicks"),
    [State('jobid-filter-cpt', 'value'),
     State('pileid-filter-cpt', 'value'),
     # State('date-filter-cpt', 'value'),
     State('cpt_graph', 'figure') ],
    prevent_initial_call=True
)
def generate_pdf_callback(n_clicks, selected_job_id,selected_pile_id, cpt_fig): #selected_date,
    if not n_clicks or not selected_pile_id:
        return no_update
    try:
        return generate_mwd_pdf_cpt(selected_job_id,selected_pile_id, cpt_fig) #selected_date,
    except Exception as e:
        print(f"PDF generation failed: {str(e)}")
        return no_update


def generate_mwd_pdf_cpt(selected_job_id,selected_pile_id,cpt_fig): #selected_date,

    # Convert Plotly figures to images
    # Enhance visibility for PDF export
    for fig in [cpt_fig]:
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


    cpt_png = BytesIO()
    pio.write_image(cpt_fig, cpt_png, format='png', scale=3)
    cpt_png.seek(0)
    # Load metadata from your sources
    cpt_data = cpt_header[selected_job_id]

    data = cpt_data[cpt_data['HoleID'] == selected_pile_id]
    job_desc = data['Job_Description'].values[0]
    project = job_desc.split('-')[0]
    location = job_desc.split('-')[1]
    # pileDiameter = prop['PileDiameter'].values[0]
    pileDiameter = data['P1_dia (inch)'].values[0]
    pile_model = data['Notes'].values[0]
    depth = round(float(data['Total Depth (feet)'].values[0]),2)
    pdf_buffer = BytesIO()
    header = PileReportHeader(
        logo_path=logo_path,
        filename=pdf_buffer,
        project=project,
        location=location,
        pile_props={
            "Pile diameter": str(pileDiameter) + " ft",
            "Pile Model": pile_model,
        },
        meta_info={
            "CPT ID": selected_pile_id,
            "depth": depth,
            "date": data['Date'].values[0],
            "elevation": data['Elevation (feet)'].values[0],
            "gwl": data["Water_Table (feet)"].values[0],
            "lat": data['Latitude (deg)'].values[0],
            "lon": data['Longitude (deg)'].values[0],
            "cone_type": "tbc",
            "operator": data['Operator'].values[0],
        },
        notes=[
            "Replace with Pile Diameter",
            'and Pile Model as "LCPC" bored piles'
        ]
    )

    header.build_pdf(images=[cpt_png])
    pdf_buffer.seek(0)

    # ✅ Encode PDF to base64
    pdf_data = base64.b64encode(pdf_buffer.read()).decode('utf-8')

    return {
        'content': pdf_data,
        'filename': f"pile_report_{selected_pile_id}.pdf",
        'type': 'application/pdf',
        'base64': True
    }


@callback(
    Output("chart-controls-collapse", "is_open"),
    Input("toggle-controls-btn", "n_clicks"),
    State("chart-controls-collapse", "is_open")
)
def toggle_chart_controls(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open


@callback(
    Output("y-axis-min", "value"),
    Output("y-axis-max", "value"),
    Input("y-axis-mode", "value"),
    [State('jobid-filter-cpt', 'value'),
     State('pileid-filter-cpt', 'value'),
     # State('date-filter-cpt', 'value')
     ],
    prevent_initial_call=True
)
def set_y_axis_range(mode,selected_jobid,selected_pileid): #,selected_date
    # Replace with your real y-data based on mode
    # Get pile data
    pile_info = jobid_cpt_data[selected_jobid]
    pile_info = pile_info[selected_pileid]
    # Determine y-axis range
    if mode =='elevation':
        y_ax_name = 'Elevation (feet)'
    else:
        y_ax_name = 'Depth (feet)'

    minD = round(min(pile_info[y_ax_name]),2)
    maxD = round(max(pile_info[y_ax_name]),2)

    return minD, maxD

@callback(
    Output("chart-type-selector", "value",allow_duplicate=True),
    Input("template-selector", "value"),
    State("chart-type-selector", "value"),
    prevent_initial_call=True,
)
def limit_chart_count(template, selected):
    max_charts = 3 if template == "3" else 4
    return selected[:max_charts]


# @callback(
#     Output("pileid-filter-cpt", "options"),
#     Output("pileid-filter-cpt", "value"),  # Clear selection
#     Input("jobid-filter-cpt", "value")
# )
# def update_pileid_options(selected_jobid):
#     if selected_jobid is None:
#         return [],None
#
#     # Replace this with your actual logic to get pile IDs for a job
#     # Example: cpt_header is a dict with job IDs as keys and list of pile IDs as values
#     df_headers = cpt_header.get(selected_jobid, [])
#     if len(df_headers)>0:
#         pile_ids = list(df_headers['HoleID'].values)
#     else:
#         return [],None
#
#     return [{"label": str(pid), "value": str(pid)} for pid in pile_ids]

@callback(
    Output("pileid-filter-cpt", "options"),
    Output("pileid-filter-cpt", "value"),
    Input("jobid-filter-cpt", "value")
)
def update_pileid_options(selected_jobid):
    if selected_jobid is None:
        return [], None

    # Safely get the DataFrame or an empty one
    df_headers = cpt_header.get(selected_jobid, pd.DataFrame())

    # Ensure 'HoleID' exists and is not empty
    if 'HoleID' not in df_headers or df_headers.empty:
        return [], None

    pile_ids = df_headers['HoleID'].dropna().unique()
    options = [{"label": str(pid), "value": str(pid)} for pid in sorted(pile_ids)]

    return options, None


@callback(
    Output("chart1-label", "children"),
    Output("chart2-label", "children"),
    Output("chart3-label", "children"),
    Output("chart4-label", "children"),
    Input("chart-type-selector", "value")
)
def update_chart_labels(selected):
    labels = []
    for i in range(4):
        if i < len(selected):
            label_text = charts_details[selected[i]][0]
        else:
            label_text = f"Chart #{i+1}"
        labels.append(html.Label(label_text, style={"color": "white"}))
    return labels


@callback(
    Output("x1-min", "value",allow_duplicate=True), Output("x1-max", "value",allow_duplicate=True),
    Output("x2-min", "value",allow_duplicate=True), Output("x2-max", "value",allow_duplicate=True),
    Output("x3-min", "value",allow_duplicate=True), Output("x3-max", "value",allow_duplicate=True),
    Output("x4-min", "value",allow_duplicate=True), Output("x4-max", "value",allow_duplicate=True),
    Input("chart-type-selector", "value"),
    [State('jobid-filter-cpt', 'value'),
     State('pileid-filter-cpt', 'value'),
     # State('date-filter-cpt', 'value'),
     ],prevent_initial_call=True,
)
def populate_x_ranges(selected,selected_jobid,selected_pileid):
    if selected_jobid is None or selected_pileid is None:
        return None,None,None,None,None,None,None,None
    pile_info = jobid_cpt_data[selected_jobid]
    pile_info = pile_info[selected_pileid]
    ranges = []
    for i in range(len(selected)):
        if i < len(selected):
            chart_key = selected[i]
            variables = charts_details[chart_key][1]
            col = variables[0]  # use first x-variable
            if col in pile_info:
                col_min = np.nanmin(pile_info[col])
                col_max = np.nanmax(pile_info[col])
            else:
                col_min, col_max = None, None
        else:
            col_min, col_max = None, None
        ranges += [col_min, col_max]
    while len(ranges)<8:
        ranges+=[0,0]

    return ranges


@callback(
    Output("load-settings-dropdown", "options",allow_duplicate=True),
    Input("save-settings-btn", "n_clicks"),
    State("profile-name", "value"),
    State("chart-type-selector", "value"),
    State("x1-min", "value"), State("x1-max", "value"),
    State("x2-min", "value"), State("x2-max", "value"),
    State("x3-min", "value"), State("x3-max", "value"),
    State("x4-min", "value"), State("x4-max", "value"),
    State("template-selector", "value"),
    prevent_initial_call=True
)
def save_settings_to_file(n_clicks, profile_name, charts, x1min, x1max, x2min, x2max, x3min, x3max, x4min, x4max,
                          template):
    if not profile_name:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"profile_{timestamp}.json"
    else:
        filename = f"{profile_name}.json"

    settings = {
        "charts": charts,
        "x_ranges": [(x1min, x1max), (x2min, x2max), (x3min, x3max), (x4min, x4max)],
        "template": template
    }

    filepath = os.path.join(SETTINGS_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(settings, f, indent=2)

    return [{"label": f, "value": f} for f in sorted(os.listdir(SETTINGS_DIR))]

# @callback(Output("chart-type-selector", "value"),
#     Output("x1-min", "value"), Output("x1-max", "value"),
#     Output("x2-min", "value"), Output("x2-max", "value"),
#     Output("x3-min", "value"), Output("x3-max", "value"),
#     Output("x4-min", "value"), Output("x4-max", "value"),
#     Output("template-selector", "value",allow_duplicate=True),
#     Input("load-settings-btn", "n_clicks"),
#     State("load-settings-dropdown", "value"),
#     prevent_initial_call=True
# )
# def load_settings_from_file(n_clicks, selected_file):
#     if not selected_file:
#         return dash.no_update
#
#     filepath = os.path.join(SETTINGS_DIR, selected_file)
#     with open(filepath, "r") as f:
#         data = json.load(f)
#
#     charts = data.get("charts", [])
#     x_ranges = data.get("x_ranges", [(None, None)] * 4)
#     template = data.get("template", "4")
#     flat_ranges = [v for pair in x_ranges for v in pair]
#
#     return charts, *flat_ranges, template

@callback(
    Output("load-settings-dropdown", "options"),
    Input("chart-type-selector", "value")  # or Input("template-selector", "value")
)
def update_profile_dropdown(_):
    return [{"label": f, "value": f} for f in sorted(os.listdir(SETTINGS_DIR))]


@callback(
    Output("chart-type-selector", "value"),
    Output("x1-min", "value"), Output("x1-max", "value"),
    Output("x2-min", "value"), Output("x2-max", "value"),
    Output("x3-min", "value"), Output("x3-max", "value"),
    Output("x4-min", "value"), Output("x4-max", "value"),
    Output("template-selector", "value", allow_duplicate=True),

    Input("load-settings-btn", "n_clicks"),
    Input("reset-controls-btn", "n_clicks"),

    State("load-settings-dropdown", "value"),
    prevent_initial_call=True
)
def handle_load_or_reset(load_clicks, reset_clicks, selected_file):
    triggered_id = ctx.triggered_id

    if triggered_id == "load-settings-btn":
        if not selected_file:
            return no_update

        filepath = os.path.join(SETTINGS_DIR, selected_file)
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            return no_update

        charts = data.get("charts", [])
        x_ranges = data.get("x_ranges", [(None, None)] * 4)
        template = data.get("template", "4")
        flat_ranges = [v for pair in x_ranges for v in pair]

        return charts, *flat_ranges, template

    elif triggered_id == "reset-controls-btn":
        # Set default values (adjust as needed)
        return (
            ["cone", "friction", "pore", "sbt"],
            None, None,
            None, None,
            None, None,
            None, None,
            "4"
        )

    return no_update