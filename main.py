import dash
import os
from dash import dcc, html #, CeleryManager
# from celery_config import celery_app
from flask import Flask
import dash_bootstrap_components as dbc
from dash import Output, Input


if '__file__' in globals():
    root_path = os.path.dirname(os.path.abspath(__file__))
else:
    # Fallback for environments where __file__ isn't available
    root_path = os.getcwd()
# if 'REDIS_URL' in os.environ:
# if True:
#     # Use Redis & Celery if REDIS_URL set as an env variable
#     background_callback_manager = CeleryManager(celery_app)
# /opt/render/project/src/.venv/lib/python3.12/site-packages/choreographer/cli/browser/chrome-linux64/chrome
server = Flask(
        __name__,
        instance_path=os.path.join(root_path, 'instance'),
        root_path=root_path,
        static_folder=os.path.join(root_path, 'assets')
    )
app = dash.Dash(__name__, server=server, use_pages=True,
                assets_folder=os.path.join(root_path, 'assets'),
                external_stylesheets=[dbc.themes.BOOTSTRAP], #"/assets/style.css",
                suppress_callback_exceptions=True,
                # prevent_initial_callbacks=True,
                # background_callback_manager=background_callback_manager,
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.2, minimum-scale=0.5,'}]
                )

# Add these right after app creation
# app.config.suppress_callback_exceptions = True
app._callback_list = []  # Clear any existing callbacks

app.title = 'MS Drill Tracker'

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("MWD", href="/", active="exact")),
        dbc.NavItem(dbc.NavLink("CPT", href="/CPT", active="exact")),
        dbc.NavItem(dbc.NavLink("Jobs Summary", href="/Metrics", active="exact")),
    ],

    brand=html.Span([
        html.Img(src=app.get_asset_url("MSB.logo.JPG"), style={'height': '70px', 'maxWidth': '100%', 'width': 'auto'}),
        html.Span("  Morris-Shea Drilling App", style={"fontSize": "1.5rem", "verticalAlign": "middle"})
    ]),
    brand_href="/",
    color="black",     # sets the background color
    dark=True,         # ensures text is light-colored for dark backgrounds
    className="mb-2",
)

layout = dbc.Container(
    [
        dcc.Location(id="url", refresh=False),
        navbar,
        dcc.Store(id='selected-jobnumber'),
        dash.page_container
    ],
    style={
        'backgroundColor': '#193153',
        'padding': '0px',
        'position': 'relative'
    },
    fluid=True
)

app.layout = layout


if __name__ == '__main__':
    app.run(debug=False)