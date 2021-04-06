import pandas as pd
import geopandas as gpd
import json
from pathlib import Path
import matplotlib.pyplot as plt
import tilemapbase
from pyproj import Proj, transform
from pprint import pprint

def create_map(state, points_gpd):
    if state not in ['Alaska','Hawaii']:
        buffer = 20
    else:
        buffer =  0.01
    # Convert points lat lng to EPSG=3857
    points_gpd.crs = "EPSG:4326"
    points_gpd = points_gpd.to_crs({"init":"EPSG:3857"})

    # Now the state boundaries
    states_shape_file = Path('gz_2010_us_040_00_500k')/'gz_2010_us_040_00_500k.shp'
    states_gpd = gpd.read_file(states_shape_file)

    # Filter the state of interest
    state_gpd = states_gpd[states_gpd['NAME']==state]

    state_gpd = state_gpd.to_crs({"init": "EPSG:3857"})
    state_gpd.set_crs(epsg=3857, inplace=True)
    # print(state_gpd.head)

    # Use tilemapbase for pretty background
    tilemapbase.start_logging()
    tilemapbase.init(create=True)
    extent = tilemapbase.extent_from_frame(state_gpd, buffer = buffer)

    # Read bounding boxes
    bounding_box = get_bounding_box(state)

    fig, ax = plt.subplots(figsize=(15,15))
    plotter = tilemapbase.Plotter(extent, tilemapbase.tiles.build_OSM(), width=1000)
    plotter.plot(ax)

    # Bounding box
    ax.set_xlim(bounding_box[0], bounding_box[1])
    ax.set_ylim(bounding_box[2], bounding_box[3])

    state_gpd.plot(ax=ax, alpha=0.3, edgecolor="black", facecolor="white")
    points_gpd.plot(ax=ax, alpha = 0.4, color="red", marker='$\\bigtriangledown$',)
    ax.figure.savefig('./data/plot1.png', bbox_inches='tight')

    return

def get_state_zips(state):

    # Load data for all the states
    test_points_file = 'us-zip-code-latitude-and-longitude.csv'
    df = pd.read_csv(test_points_file,sep=';')
    df = df.drop('geopoint',axis=1)

    # Restrrict to zip codes that belong to the state
    df = df[df['State']==state]
    df = df.reset_index(drop=True)

    # Make it into a geopandas GeoDataFrame
    gdf = gpd.GeoDataFrame(\
            df, geometry = gpd.points_from_xy(df.Longitude, df.Latitude))
    gdf = gdf.drop(['Latitude','Longitude'], axis=1)
    return gdf

def get_bounding_box(state):
    # Read the state bounding boxes (Maybe replace this with a dict)
    # In any case this values are in latlong
    state_bb_file = 'states_bounding_boxes.csv'
    states_bb_df = pd.read_csv(state_bb_file)
    state_bb_df = states_bb_df[states_bb_df['NAME']==state]

    # Read the values for the state (There has to be a more elegant way)

    lat_min = list(state_bb_df.ymin)[0]
    lat_max = list(state_bb_df.ymax)[0]
    lng_min = list(state_bb_df.xmin)[0]
    lng_max = list(state_bb_df.xmax)[0]

    if state not in ['Alaska', 'Hawaii']:
        lat_min *= 0.99
        lat_max *= 1.01
        lng_min *= 1.01
        lng_max *= 0.99
    elif state=='Alaska':
        lat_min = 50
        lat_max = 72
        lng_min = -179.9
        lng_max = -125
    elif state=='Hawaii':
        lat_min = 18
        lat_max = 23
        lng_min = -162
        lng_max = -154

    outProj = Proj(init='epsg:3857')
    inProj = Proj(init='epsg:4326')

    #print('Latitudes: ', lat_min, lat_max)
    #print('Longitudes: ',lng_min, lng_max)

    x_min,y_min = transform(inProj, outProj, lng_min, lat_min)
    x_max,y_max = transform(inProj, outProj, lng_max, lat_max)

    return [x_min, x_max, y_min, y_max]
