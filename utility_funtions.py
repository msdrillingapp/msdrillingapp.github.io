import numpy as np
import pandas as pd
import dash_leaflet as dl
import json
import os

file_path = os.path.join(os.getcwd(), "assets",)
geojson_folder = os.path.join(file_path,'data')
def filter_none(lst):
    return filter(lambda x: not x is None, lst)

# Function to load all GeoJSON files dynamically
def load_geojson_data():
    all_data = []
    pile_data = {}
    markers = []
    latitudes = []
    longitudes =[]
    for filename in os.listdir(geojson_folder):
        if filename.endswith(".json"):
            # file_date = filename.replace("header", "").replace(".json", "").strip()  # Extract date from filename
            file_path = os.path.join(geojson_folder, filename)

            with open(file_path, "r", encoding = "utf-8") as f:
                geojson_data = json.load(f)

            features = geojson_data.get("features", [])

            for feature in features:
                properties = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                coords = geometry.get("coordinates", [])
                # PileCode": "PP",  "PileCode": "PRODUCTION PILE",
                # "PileCode": "TP",  "PileCode": "TEST PILE",
                # "PileCode": "RP", "PileCode": "REACTION PILE",
                # "PileCode": "PB", "PileCode": "PROBE",
                if coords and len(coords) >= 2:
                    lat, lon = coords[:2]  # Ensure correct coordinate order
                    properties["latitude"] = lat
                    properties["longitude"] = lon
                    latitudes.append(lat)
                    longitudes.append(lon)
                    try:
                        date= pd.to_datetime(properties['Time']).date().strftime(format='%Y-%m-%d')
                    except:
                        date = 'NA'
                    properties["date"] = date # Store the date from the filename
                    # PileCode - PP = circle , TestPile = square , Reaction = Octagon
                    pile_code = properties['PileCode']
                    # print(pile_code)
                    pile_status = properties['PileStatus']
                    pile_id = properties['PileID']
                    if not lat is None and not lon is None:
                        # Assign different marker styles
                        if pile_code.lower() == "PRODUCTION PILE".lower():  # Circle
                            marker = dl.CircleMarker(
                                center=(lat, lon),
                                radius=5, color="blue", fill=True,
                                children=[
                                    dl.Tooltip(f"PileID: {pile_id}, Status: {pile_status}")]
                            )

                        elif pile_code.lower() ==  "TEST PILE".lower():  # Square (Using a rectangle as an approximation)
                            marker = dl.Rectangle(
                                bounds=[(lat - 0.0001, lon - 0.0001),
                                        (lat + 0.0001, lon + 0.0001)],
                                color="green", fill=True,
                                children=[
                                    dl.Tooltip(f"PileID: {pile_id}, Status: {pile_status}")]
                            )

                        elif pile_code.lower() == "REACTION PILE".lower():  # Octagon (Using a custom SVG marker)
                            marker = dl.Marker(
                                position=(lat, lon),
                                icon={
                                    "iconUrl": "https://upload.wikimedia.org/wikipedia/commons/4/4f/Octagon_icon.svg",
                                    "iconSize": [20, 20]  # Adjust size
                                },
                                children=[
                                    dl.Tooltip(f"PileID: {pile_id}, Status: {pile_status}")]
                            )

                        else:  # Default marker for other PileCodes PB "PROBE"
                            marker = dl.Marker(
                                position=(lat, lon),
                                children=[
                                    dl.Tooltip(f"PileID: {pile_id}, Status: {pile_status}")]
                            )

                        markers.append(marker)

                    else:
                        continue
                    # Store time-series data separately for graph plotting
                    pile_id = properties.get("PileID")
                    if pile_id and "Data" in properties:
                        pile_data.setdefault(pile_id, {})[properties['date']] = {
                            "Time": properties["Data"].get("Time", []),
                            "Strokes": properties["Data"].get("Strokes", []),
                            "Depth": properties["Data"].get("Depth", [])
                        }

                    all_data.append(properties)

    return pd.DataFrame(all_data), pile_data,latitudes,longitudes,markers


def get_plotting_zoom_level_and_center_coordinates_from_lonlat_tuples(longitudes=None, latitudes=None):
    """Function documentation:\n
    Returns the appropriate zoom-level for these plotly-mapbox-graphics along with
    the center coordinate tuple of all provided coordinate tuples.
    """

    # Check whether both latitudes and longitudes have been passed,
    # or if the list lenghts don't match
    if ((latitudes is None or longitudes is None)
            or (len(latitudes) != len(longitudes))):
        # Otherwise, return the default values of 0 zoom and the coordinate origin as center point
        return 0, (0, 0)

    # Get the boundary-box
    b_box = {}
    b_box['height'] = latitudes.max()-latitudes.min()
    b_box['width'] = longitudes.max()-longitudes.min()
    b_box['center']= (np.mean(longitudes), np.mean(latitudes))

    # get the area of the bounding box in order to calculate a zoom-level
    area = b_box['height'] * b_box['width']

    # * 1D-linear interpolation with numpy:
    # - Pass the area as the only x-value and not as a list, in order to return a scalar as well
    # - The x-points "xp" should be in parts in comparable order of magnitude of the given area
    # - The zpom-levels are adapted to the areas, i.e. start with the smallest area possible of 0
    # which leads to the highest possible zoom value 20, and so forth decreasing with increasing areas
    # as these variables are antiproportional
    zoom = np.interp(x=area,
                     xp=[0, 5**-10, 4**-10, 3**-10, 2**-10, 1**-10, 1**-5],
                     fp=[20, 15,    14,     13,     12,     7,      5])

    # Finally, return the zoom level and the associated boundary-box center coordinates
    return zoom, b_box['center']