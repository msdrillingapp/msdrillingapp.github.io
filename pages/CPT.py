import dash
from dash import dcc, html, Output, Input, State, ClientsideFunction, callback,no_update
from functions import properties_df, jobid_pile_data,cpt_header
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import base64
from io import BytesIO
from reportlab.platypus import Image
from reportlab.lib.units import inch
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

dash.register_page(
    __name__,
    path_template="/CPT",
    path="/CPT",
)
import os
logo_path = os.path.join(os.getcwd(), "assets","MSB.logo.JPG" )

# =================================================================
# ========== FUNCTIONS =============================================
# =================================================================

# Helper function to find closest x value and create annotation
def get_closest_x(y_series, x_series, target_y):
    idx = (y_series - target_y).abs().idxmin()
    return x_series.iloc[idx]#, idx
def get_filters_cpt(properties_df):
    df = properties_df.copy()
    df = df[df['PileID'].str.startswith('PB-CPT', na=False)]
    filters = html.Div([
        dbc.Row([
            dbc.Col(
                dcc.Dropdown(
                id="jobid-filter-cpt",
                options=[{"label": str(r), "value": str(r)} for r in df["JobNumber"].dropna().unique()],
                placeholder="Filter by JobID",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            )),
            dbc.Col(dcc.Dropdown(
                id="date-filter-cpt",
                options=[{"label": d, "value": d} for d in sorted(df["date"].unique())],
                placeholder="Select a Date",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            )),
            dbc.Col(dcc.Dropdown(
                id="pileid-filter-cpt",
                options=[{"label": str(p), "value": str(p)} for p in df["PileID"].dropna().unique()],
                placeholder="Filter by PileID",
                style={'width': '150px', 'marginBottom': '10px', 'marginRight': '10px', 'marginLeft': '10px'},
                className="dark-dropdown"
            ))
        ]),
    ], style={'marginBottom': '10px', 'display': 'flex', 'justifyContent': 'center'})
    return filters


def create_cpt_charts(pile_info, use_depth: bool = False, y_value: float = None):
    if use_depth:
        y_ax_name = 'Depth (feet)'
    else:
        y_ax_name = 'Elevation (feet)'

    minD = min(pile_info[y_ax_name]) - 5
    maxD = max(pile_info[y_ax_name]) + 5

    fig = make_subplots(
        rows=1,
        cols=4,
        shared_yaxes=True,
        subplot_titles=(
            "Cone resistance<br>",
            "Friction Ratio<br>",
            "Pore Pressure<br>",
            "Soil Behaviour Type<br>"
        ),
        horizontal_spacing=0.05
    )

    y_ax = pile_info[y_ax_name]

    # Add traces
    fig.add_trace(
        go.Scatter(x=pile_info['q_c (tsf)'], y=y_ax, mode='lines', line=dict(color='red', width=2), name='q_c',
                   showlegend=True),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=pile_info['q_t (tsf)'], y=y_ax, mode='lines', line=dict(color='blue', width=2), name='q_t',
                   ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(x=pile_info['R_f (%)'], y=y_ax, mode='lines', line=dict(color='red', width=2), showlegend=True,
                   name='R_f (%)'),
        row=1, col=2
    )
    fig.add_trace(
        go.Scatter(x=pile_info['U_2 (ft-head)'], y=y_ax, mode='lines', line=dict(color='red', width=2), showlegend=True,
                   name='U_2'),
        row=1, col=3
    )
    fig.add_trace(
        go.Scatter(x=pile_info['U_0 (ft-head)'], y=y_ax, mode='lines', line=dict(color='blue', width=2),
                   name='U_0'),
        row=1, col=3
    )
    # unique_zone = np.array(pile_info['Zone_Icn'])
    # unique_zone = np.unique(unique_zone)
    zones = pile_info['Zone_Icn']
    zones = list(np.nan_to_num(zones))
    colors = [zone_colors[i] for i in zones]
    fig.add_trace(
        go.Bar(
            x=pile_info['Zone_Icn'],
            y=y_ax,
            orientation='h',
            marker=dict(
                color=colors,
                line=dict(color='rgba(0,0,0,0)', width=0) # no border
            ),
            showlegend=False,
            hoverinfo='text',
            hovertext=pile_info['SBT_Icn'],
            base=0,  # This ensures bars start at 0
        ),
        row=1, col=4
    )

    # Add horizontal line and value annotations if y_value is provided
    if y_value is not None:
        filtered_data = {k: pile_info[k] for k in columns_cpt if k in pile_info}
        # Find the closest data point to the selected y_value for each trace
        df = pd.DataFrame(filtered_data)

        # Add horizontal line to each subplot
        for col in range(1, 5):
            fig.add_hline(
                y=y_value,
                line_dash="dot",
                line_color="cyan",
                line_width=2,
                row=1, col=col
            )

            # Add value annotations for each trace in the subplot
            if col == 1:  # Cone resistance (q_c and q_t)
                qc_x = get_closest_x(df[y_ax_name], df['q_c (tsf)'], y_value)
                qt_x = get_closest_x(df[y_ax_name], df['q_t (tsf)'], y_value)

                fig.add_annotation(
                    x=qc_x, y=y_value,
                    text=f"q_c: {qc_x:.2f}",
                    showarrow=True,
                    arrowhead=1,
                    ax=20,
                    ay=10,
                    bgcolor="rgba(255,0,0,0.7)",
                    row=1, col=1
                )
                fig.add_annotation(
                    x=qt_x, y=y_value,
                    text=f"q_t: {qt_x:.2f}",
                    showarrow=True,
                    arrowhead=1,
                    ax=20,
                    ay=-10,
                    bgcolor="rgba(0,0,255,0.7)",
                    row=1, col=1
                )

            elif col == 2:  # Friction Ratio (R_f)
                rf_x = get_closest_x(df[y_ax_name], df['R_f (%)'], y_value)
                fig.add_annotation(
                    x=rf_x, y=y_value,
                    text=f"R_f: {rf_x:.2f}%",
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=10,
                    bgcolor="rgba(255,0,0,0.7)",
                    row=1, col=2
                )

            elif col == 3:  # Pore Pressure (U_2 and U_0)
                u2_x = get_closest_x(df[y_ax_name], df['U_2 (ft-head)'], y_value)
                u0_x = get_closest_x(df[y_ax_name], df['U_0 (ft-head)'], y_value)

                fig.add_annotation(
                    x=u2_x, y=y_value,
                    text=f"U_2: {u2_x:.2f}",
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=10,
                    bgcolor="rgba(255,0,0,0.7)",
                    row=1, col=3
                )
                fig.add_annotation(
                    x=u0_x, y=y_value,
                    text=f"U_0: {u0_x:.2f}",
                    showarrow=True,
                    arrowhead=1,
                    ax=0,
                    ay=-10,
                    bgcolor="rgba(0,0,255,0.7)",
                    row=1, col=3
                )

    # Update layout
    fig.update_layout(
        yaxis_title=y_ax_name,
        plot_bgcolor="#193153",
        paper_bgcolor="#193153",
        font=dict(color="white"),
        showlegend=False,
        # legend=dict(
        #     orientation="h",
        #     yanchor="top",
        #     y=-0.3,
        #     xanchor="center",
        #     x=0.5,
        #     font=dict(size=11),
        #     itemwidth=30,
        # ),
        dragmode="select",
        autosize=True,
        margin=dict(l=50, r=50, b=50, t=50, pad=4)
    )
    x_ann_q_t = max(pile_info['q_t (tsf)'])-10
    fig.add_annotation(
        xref="x1", yref="paper",
        x=x_ann_q_t, y=5,
        text="<span style='color:red'>q_c</span><br><span style='color:blue'>q_t</span>",
        showarrow=False,
        align='right',
        font=dict(size=11),
        bgcolor="rgba(0,0,0,0)",
        row=1, col=1
    )
    x_ann_RF = max(pile_info['R_f (%)'])
    fig.add_annotation(
        xref="x1", yref="paper",
        x=x_ann_RF, y=5,
        text="<span style='color:red'>R_f (%)</span><br>",
        showarrow=False,
        align='right',
        font=dict(size=11),
        bgcolor="rgba(0,0,0,0)",
        row=1, col=2
    )
    # U_0 (ft-head)
    x_ann_U0 = max(pile_info['U_2 (ft-head)'])
    fig.add_annotation(
        xref="x1", yref="paper",
        x=x_ann_U0, y=5,
        text="<span style='color:red'>U_2</span><br><span style='color:blue'>U_0</span>",
        showarrow=False,
        align='right',
        font=dict(size=11),
        bgcolor="rgba(0,0,0,0)",
        row=1, col=3
    )

    fig.update_annotations(font_size=11)
    fig.update_yaxes(range=[minD, maxD])

    # Configure gridlines for each subplot
    for i in range(1, 5):
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
        fig.update_xaxes(title_text="tsf", row=1, col=1)
        fig.update_xaxes(title_text="%", row=1, col=2)
        fig.update_xaxes(title_text="ft-head", row=1, col=3)
        fig.update_xaxes(title_text="SBT (Robertson, 2010)", row=1, col=4)



    return fig


def add_cpt_charts():
    charts = dbc.Collapse(
        html.Div([
            html.Button("Download PDF for PileID", id='download-pdf-btn-cpt', disabled=True),
            dbc.Row([
                dbc.Col(
                    dcc.Graph(
                        id="cpt_graph",
                        style={"backgroundColor": "#193153", 'width': '100%', 'marginBottom': '5px'},
                        config={'displayModeBar': False}
                    ),
                    xs=12, sm=12, md=12, lg=12, xl=12
                ),
            ]),
            dcc.Download(id="download-pdf-cpt"),
            # Add the slider below the graph
            dbc.Row([
                dbc.Col(
                    dcc.Slider(
                        id='y-value-slider',
                        min=0,
                        max=100,
                        value=50,
                        step=0.1,
                        marks=None,
                        tooltip={"placement": "bottom", "always_visible": True},
                        className="custom-slider"
                    ),
                    width=12
                )
            ], style={'marginTop': '20px', 'padding': '0 20px'}),
            # Store the current y-value
            dcc.Store(id='current-y-value')
        ]),
        id="collapse-plots-cpt",
        is_open=False
    )
    return charts

def add_chart_controls():
    layout = html.Div([
        html.H4("CPT Chart Controls", style={"color": "white"}),

        # Dropdown to select Y-axis mode
        html.Div([
            html.Label("Y-Axis Scale:", style={"color": "white"}),
            dcc.Dropdown(
                id="y-axis-mode",
                options=[
                    {"label": "Elevation (feet)", "value": "elevation"},
                    {"label": "Depth (feet)", "value": "depth"}
                ],
                value="elevation",
                clearable=False,
                className="dark-dropdown"
            )
        ], style={"width": "300px", "margin-bottom": "20px"}),

        # Inputs for x-axis ranges
        html.Div([
            html.Label("X-Axis Ranges (Min/Max):", style={"color": "white"}),
            dbc.Row([
                dbc.Col([
                    html.Label("Cone Resistance (tsf)", style={"color": "white"}),
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
                    html.Label("Friction Ratio (%)", style={"color": "white"}),
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
                    html.Label("Pore Pressure (ft-head)", style={"color": "white"}),
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
                    html.Label("Soil Behaviour Type", style={"color": "white"}),
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

        html.Br(),
        dbc.Button("Update Chart", id="update-btn", color="primary", className="mb-2"),

    ])

    return layout
# =================================================================
# =================================================================
# =================================================================
flts = get_filters_cpt(properties_df)
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

# Custom CSS for the slider
app = dash.get_app()
app.clientside_callback(
    """
    function(href) {
        var style = document.createElement('style');
        style.innerHTML = `
            .custom-slider .rc-slider-track {
                background-color: #4a90e2;
            }
            .custom-slider .rc-slider-handle {
                border-color: #4a90e2;
            }
            .custom-slider .rc-slider-tooltip-inner {
                background-color: #4a90e2;
                color: white;
            }
        `;
        document.head.appendChild(style);
        return window.innerWidth;
    }
    """,
    Output('window-size', 'data'),
    Input('url', 'href')
)


# =================================================================
# ========================CALLBACKS ===============================
# =================================================================
@callback(
    Output("cpt_graph", "figure"),
    Output('download-pdf-btn-cpt', 'disabled'),
    Output('y-value-slider', 'min'),
    Output('y-value-slider', 'max'),
    Output('y-value-slider', 'value'),
    Output('current-y-value', 'data'),
    Input("update-btn", "n_clicks"),
    Input('pileid-filter-cpt', 'value'),
    Input('date-filter-cpt', 'value'),
    Input('y-value-slider', 'value'),
    Input('cpt_graph', 'selectedData'),
    Input('window-size', 'data'),
    State("jobid-filter-cpt", "value"),
    State('current-y-value', 'data'),
    State("y-axis-mode", "value"),
    State("x1-min", "value"), State("x1-max", "value"),
    State("x2-min", "value"), State("x2-max", "value"),
    State("x3-min", "value"), State("x3-max", "value"),
    State("x4-min", "value"), State("x4-max", "value"),
)
def update_cpt_graph(n_clicks,selected_pileid, selected_date, slider_value, selected_data, window_size, selected_jobid,
                     current_y_value, y_mode, x1_min, x1_max, x2_min, x2_max, x3_min, x3_max, x4_min, x4_max):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    if not selected_pileid or not selected_date:
        return go.Figure(layout={"plot_bgcolor": "#193153", "paper_bgcolor": "#193153"}), True, 0, 100, 50, None

    use_depth = (y_mode == "depth")

    # Build a dict of x-axis limits
    x_limits = {
        1: (x1_min, x1_max),
        2: (x2_min, x2_max),
        3: (x3_min, x3_max),
        4: (x4_min, x4_max),
    }

    # Get pile data
    pile_data = jobid_pile_data[selected_jobid]
    pile_info = pile_data[selected_pileid][selected_date]

    # Determine y-axis range
    y_ax_name = 'Elevation (feet)'  # or 'Depth (feet)' based on your logic
    minD = min(pile_info[y_ax_name]) - 5
    maxD = max(pile_info[y_ax_name]) + 5

    # Handle y-value updates
    y_value = current_y_value if current_y_value is not None else (minD + maxD) / 2

    if trigger_id == 'y-value-slider':
        y_value = slider_value
    elif trigger_id == 'cpt_graph' and selected_data is not None:
        y_values = [point['y'] for point in selected_data['points']]
        if y_values:
            y_value = np.mean(y_values)

    # Create figure with current y-value and annotations
    fig = create_cpt_charts(pile_info,use_depth=use_depth, y_value=y_value)

    # Apply x-axis ranges to each subplot
    for i in range(1, 5):
        min_val, max_val = x_limits[i]
        if min_val is not None and max_val is not None:
            fig.update_xaxes(range=[min_val, max_val], row=1, col=i)

    return fig, False, minD, maxD, y_value, y_value



#
#
# @app.callback(
#     Output("cpt-graph", "figure"),
#     Input("update-btn", "n_clicks"),
#     State("y-axis-mode", "value"),
#     State("x1-min", "value"), State("x1-max", "value"),
#     State("x2-min", "value"), State("x2-max", "value"),
#     State("x3-min", "value"), State("x3-max", "value"),
#     State("x4-min", "value"), State("x4-max", "value"),
#     State("jobid-filter-cpt", "value"),
#     State('pileid-filter-cpt', 'value'),
#     State('date-filter-cpt', 'value'),
# )
# def update_cpt_chart(n_clicks, y_mode, x1_min, x1_max, x2_min, x2_max, x3_min, x3_max, x4_min, x4_max,selected_jobid,selected_pileid,selected_date):
#     use_depth = (y_mode == "depth")
#
#     # Build a dict of x-axis limits
#     x_limits = {
#         1: (x1_min, x1_max),
#         2: (x2_min, x2_max),
#         3: (x3_min, x3_max),
#         4: (x4_min, x4_max),
#     }
#     # Get pile data
#     pile_data = jobid_pile_data[selected_jobid]
#     pile_info = pile_data[selected_pileid][selected_date]
#     # Assume pile_info and y_value come from elsewhere or global context
#     fig = create_cpt_charts(pile_info, use_depth=use_depth)
#
#     # Apply x-axis ranges to each subplot
#     for i in range(1, 5):
#         min_val, max_val = x_limits[i]
#         if min_val is not None and max_val is not None:
#             fig.update_xaxes(range=[min_val, max_val], row=1, col=i)
#
#     return fig


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
State('date-filter-cpt', 'value'),
     State('cpt_graph', 'figure'),
 ],
    prevent_initial_call=True
)
def generate_pdf_callback(n_clicks, selected_job_id,selected_pile_id, selected_date,cpt_fig):
    if not n_clicks or not selected_pile_id:
        return no_update
    try:
        return generate_mwd_pdf_cpt(selected_job_id,selected_pile_id,selected_date, cpt_fig)
        # return dcc.send_file(filepath)
    except Exception as e:
        print(f"PDF generation failed: {str(e)}")
        return no_update


def generate_mwd_pdf_cpt(selected_job_id,selected_pile_id,selected_date,cpt_fig):

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


    # from plotly.io import to_image
    # fig = go.Figure(cpt_fig)
    # cpt_png = BytesIO(to_image(fig, format="png", scale=3))
    # cpt_png.seek(0)
    import plotly.io as pio

    cpt_png = BytesIO()
    pio.write_image(cpt_fig, cpt_png, format='png', scale=3)
    cpt_png.seek(0)
    # Load metadata from your sources
    cpt_data = cpt_header[selected_job_id]

    pile_suffix = selected_pile_id.split('CPT')[-1]  # e.g., "1"
    hole_id = f"CPT-{int(pile_suffix):02d}"  # --> "CPT-01"
    data = cpt_data[cpt_data['HoleID'] == hole_id]

    prop = properties_df[properties_df['JobNumber']==selected_job_id].copy()
    prop = prop[prop['PileID']==selected_pile_id]
    job_desc = data['Job_Description'].values[0]
    project = job_desc.split(',')[0]
    location = job_desc.split(',')[1] + ', '+job_desc.split(',')[-1]
    pileDiameter = prop['PileDiameter'].values[0]
    pile_model = data['Notes'].values[0]

    # output_dir = "C:\\Temp"
    # os.makedirs(output_dir, exist_ok=True)
    # output_path = f"C:\\Temp\\pile_report_{selected_pile_id}.pdf"
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
            "depth": data['Total Depth (feet)'].values[0],
            "date": selected_date,
            "elevation": data['Elevation (feet)'].values[0],
            "gwl": data["Water_Table (feet)"].values[0],
            "lat": data['Latitude (deg)'].values[0],
            "lon": data['Longitude (deg)'].values[0],
            # "cone_type": "1-CPT009-15",
            "operator": prop['Operator'].values[0],
        },
        notes=[
            "Replace with Pile Diameter",
            'and Pile Model as "LCPC" bored piles'
        ]
    )

    # header.build_pdf(images=[Image(cpt_png, width=3 * inch, height=5 * inch)])
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
    # return dcc.send_bytes(pdf_buffer.read(), filename=f"pile_report_{selected_pile_id}.pdf")




    # # Build PDF
    # file_name = 'JobID_' + str(selected_row.get('JobID', '')) + '_PileID_' + str(
    #     selected_row.get('PileID', '')) + '_Time_' + str(selected_row.get('Time', '')) + '.pdf'
    # doc.build(story)
    # buffer.seek(0)
    # pdf_data = base64.b64encode(buffer.read()).decode('utf-8')
    # return {
    #     'content': pdf_data,
    #     'filename': file_name,
    #     'type': 'application/pdf',
    #     'base64': True
    # }
    return
