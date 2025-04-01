import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import dash
import dash_table
from dash_table.Format import Format, Group
import dash_table.FormatTemplate as FormatTemplate
from datetime import datetime as dt
from main import app


####################################################################################################
# 000 - DEFINE REUSABLE COMPONENTS AS FUNCTIONS
####################################################################################################

#####################
# Header with logo
def get_header():
    title_text = "Morris-Shea Drilling App"
    header = html.Div([
        html.H1(title_text, style={'textAlign': 'left', 'color': 'white', 'flex': '1'}),
        html.Img(src="/assets/MSB.logo.JPG",
                 style={'height': '80px', 'position': 'absolute', 'top': '10px', 'right': '20px'}
                 )
    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}),

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
