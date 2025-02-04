import xarray as xr
import holoviews as hv
import geoviews as gv
from cartopy import crs as ccrs
import panel as pn
import streamlit as st
import numpy as np

# Initialize Holoviews and Geoviews extensions
hv.extension('bokeh')
gv.extension('bokeh')

# Path to the NetCDF file
NETCDF_FILE = "all_gwl_humidex_max_with_dates.nc"

# Cache the loading of data
@st.cache_data
def load_data(file_path):
    """Load the NetCDF dataset."""
    return xr.open_dataset(file_path)

# Load the dataset
ds = load_data(NETCDF_FILE)

# Create GWL and Year selectors
gwl_options = list(ds["gwl"].values)
default_gwl = gwl_options[0]

gwl_selector = pn.widgets.Select(name="Select GWL", options=gwl_options, value=default_gwl)

# Function to get the year range for a selected GWL
def get_years_for_gwl(gwl):
    return list(ds["year"].values)

# Create a year selector that updates dynamically
year_slider = pn.widgets.IntSlider(name="Select Year", start=0, end=0, value=0)

def update_year_slider(event):
    gwl = event.new
    years = get_years_for_gwl(gwl)
    year_slider.start = int(years[0])
    year_slider.end = int(years[-1])
    year_slider.value = int(years[0])

gwl_selector.param.watch(update_year_slider, "value")

# Plotting function
def plot_humidex(gwl, year):
    """Generate the interactive plot for the given GWL and year."""
    # Extract data for the selected GWL and year
    humidex_field = ds["humidex_max"].sel(gwl=gwl, year=year)
    lat_percentile = ds["lat_percentile"].sel(gwl=gwl, year=year).values
    lon_percentile = ds["lon_percentile"].sel(gwl=gwl, year=year).values
    lat_abs_max = ds["lat_abs_max"].sel(gwl=gwl, year=year).values
    lon_abs_max = ds["lon_abs_max"].sel(gwl=gwl, year=year).values

    # Create the base plot
    gv_data = gv.Dataset(
        (ds["longitude"], ds["latitude"], humidex_field),
        kdims=["Longitude", "Latitude"],
        vdims=["Humidex"],
        crs=ccrs.PlateCarree()
    )

    quadmesh = gv_data.to(gv.QuadMesh, ["Longitude", "Latitude"], "Humidex").opts(
        cmap="RdBu_r",
        colorbar=True,
        clim=(20, 50),
        tools=["hover"],
        projection=ccrs.PlateCarree()
    )

    # Add points for percentile and absolute maxima
    point_data = [
        (lon_percentile, lat_percentile, "99.9th Percentile", "cyan"),
        (lon_abs_max, lat_abs_max, "Absolute Max", "black"),
    ]
    markers = gv.Points(
        point_data,
        kdims=["Longitude", "Latitude"],
        vdims=["Description", "Color"],
        crs=ccrs.PlateCarree()
    ).opts(size=10, marker="x", color="Color", show_legend=True)

    # Add caption
    date_of_max = ds["date_of_max_percentile"].sel(gwl=gwl, year=year).values.item()
    caption = f"""
    Ensemble 01, Date: {date_of_max}\n
    99.9th Percentile Max: {humidex_field.max().values:.2f}°C | Absolute Max: {humidex_field.max().values:.2f}°C\n
    99.9th Percentile Location: ({lat_percentile:.2f}, {lon_percentile:.2f})\n
    Absolute Max Location: ({lat_abs_max:.2f}, {lon_abs_max:.2f})
    """

    return hv.Div(caption) + (quadmesh * markers)

# Create an interactive panel layout
def interactive_plot(gwl, year):
    return plot_humidex(gwl, year)

# Streamlit app layout
st.title("Interactive Humidex Viewer")
st.sidebar.header("Controls")

# Sidebar inputs
selected_gwl = st.sidebar.selectbox("Select GWL", gwl_options)
years = get_years_for_gwl(selected_gwl)
selected_year = st.sidebar.slider("Select Year", min(years), max(years), min(years))

# Display the plot
plot = plot_humidex(selected_gwl, selected_year)
st.bokeh_chart(hv.render(plot, backend="bokeh"), use_container_width=True)
