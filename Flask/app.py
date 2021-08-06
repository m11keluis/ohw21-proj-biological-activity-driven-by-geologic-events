from flask import Flask, render_template, request, url_for, session
from forms import QueryInputForm
from erddapy import ERDDAP
import pandas as pd
from datetime import datetime,timedelta
import numpy as np
import os
import json
import plotly
import plotly.express as px

app = Flask(__name__)
app.secret_key = 'random_key!'

def extract_coastWatch(dataset_id, start_date, end_date, mount_lat=45.95, mount_lon=-130, deg=2, node="CSWC"):
    
    from erddapy import ERDDAP
    import json

    # Initialize CoastWatch Server
    coastWatch_e = ERDDAP(
        server=node,  
        protocol="griddap",
    )

    coastWatch_e.dataset_id = (
        dataset_id
    )

    coastWatch_e.griddap_initialize()

    # Set Constraints: Bounding Box & Time
    min_lon, max_lon = mount_lon+deg, mount_lon-deg
    min_lat, max_lat = mount_lat-deg, mount_lat+deg
    
    # Dates in UTC: %Y-%m-%dT%H:%M:%S.%fZ
    start_time="%sT00:00:00Z" % (start_date)
    end_time="%sT00:00:00Z" % (end_date)    

    coastWatch_e.constraints["time>="] = start_date
    coastWatch_e.constraints["time<="] = end_date 
    coastWatch_e.constraints["latitude>="] = min_lat
    coastWatch_e.constraints["latitude<="] = max_lat
    coastWatch_e.constraints["longitude>="] = max_lon
    coastWatch_e.constraints["longitude<="] = min_lon
    
    # Read to xarray
    ds = coastWatch_e.to_xarray()

    return ds

def extract_OOI(dataset_id, start_date, end_date):
    
    server = "https://erddap.dataexplorer.oceanobservatories.org/erddap"
    e = ERDDAP(server=server, protocol="tabledap")
    e.dataset_id = database
    e.constraints = {
        "time>=": start_date,
        "time<=": end_date 
    }
    e.variables = ['time', select_var]

    print(start_date, end_date, select_var, database, e)
    df = e.to_pandas()
    df['time (UTC)'] = pd.to_datetime(df['time (UTC)'])

    print(df.head())


    return df

def plot_satellite(xr, select_var):

    import hvplot.xarray

    if select_var == 'chlorophyll':
        
        xr = xr.squeeze("altitude")
        xr.chlorophyll.hvplot(
        groupby="time",  # adds a widget for time
        clim=(0, 5),  # sets colormap limits
        widget_type="scrubber",
        widget_location="bottom",
    )
    
    else:
        
        xr.SST.hvplot(
        groupby="time",  # adds a widget for time
        widget_type="scrubber",
        widget_location="bottom",
    )
    

e_databases = {
    'iespres': 'ooi-rs03axbs-lj03a-05-hpiesa301',
    'mass_concentration_of_chlorophyll_a_in_sea_water': 'ooi-rs03axps-pc03a-4c-flordd303',
    'sea_water_ph_reported_on_total_scale': 'ooi-rs03axps-pc03a-4b-phsena302',
    'sea_water_temperature': 'ooi-rs03axps-pc03a-4a-ctdpfa303',
    'sea_water_practical_salinity': 'ooi-rs03axps-pc03a-4a-ctdpfa303',
    'mole_concentration_of_dissolved_molecular_oxygen_in_sea_water': 'ooi-rs03axps-pc03a-4a-ctdpfa303',
    'sea_water_density': 'ooi-rs03axps-pc03a-4a-ctdpfa303',
    'sea_water_pressure': 'ooi-rs03axps-pc03a-4a-ctdpfa303',
    'sea_water_pressure_at_sea_floor': 'ooi-rs03axbs-mj03a-06-presta301',
    'SST':'jplG1SST',
    'chlorophyll':'erdMWchla14day_LonPM180'
    
    
}


satelliteVar_list = ['SST', 'chlorophyll']

@app.route('/', methods = ['GET', 'POST'])
def index():
    query_form = QueryInputForm(request.form)

    if request.method == 'POST':
        if 'start_date' in request.form and query_form.validate_on_submit():
            start_date = request.form['start_date'] + "T00:00:00Z"
            end_date = request.form['end_date'] + "T23:59:59Z"
            select_var = request.form['select_var']
            database = e_databases[select_var]

            # Initialize CoastWatch Server for Satellite Imagery
            if select_var in satelliteVar_list:
                
                sat_xr = extract_coastWatch(database,start_date, end_date)
                plot_satellite(sat_xr, select_var)
                
            else:
            
            # Initialize OOI Data
                ooi_xr = extract_OOI (database,start_date, end_date)



    return render_template('index.html', query_form = query_form)


def fix_date(da):
    da = da.assign(time=([datetime(1970,1,1) + timedelta(seconds=second) for second in da.time.data]))
    return da


if __name__ == '__main__':
	app.run(host = '127.0.0.1', port = 5000)