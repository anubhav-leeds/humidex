import os
import streamlit as st
import xarray as xr
import holoviews as hv
import geoviews as gv
from holoviews import opts

# Enable Bokeh backend for HoloViews
hv.extension("bokeh")
gv.extension("bokeh")

# Set the title of the app
st.title("Interactive Humidex Viewer")

try:
    # Debugging information
    st.subheader("Debugging Information")
    st.write("Current working directory:", os.getcwd())
    st.write("Files in directory:", os.listdir())

    # File path to the NetCDF data
    FILE_PATH = "all_gwl_humidex_max_with_dates.nc"
    if not os.path.exists(FILE_PATH):
        st.error(f"File not found: {FILE_PATH}")
        st.stop()

    # Load the NetCDF dataset
    ds = xr.open_dataset(FILE_PATH)

    # Dropdown menu for GWL selection
    gwl_options = list(ds["gwl"].values)
    gwl = st.selectbox("Select GWL", options=gwl_options, index=0)

    # Dropdown menu for year selection (mapped to actual years)
    start_year = 1995 if gwl != "4.0" else 2052  # Adjust this for each GWL
    year_options = list(range(start_year, start_year + 20))
    year = st.selectbox("Select Year", options=year_options)

    # Convert selected year to year index
    year_index = year - start_year

    # Extract data for the selected GWL and year
    humidex_field = ds["humidex_max"].sel(gwl=gwl, year=year_index)
    lat_percentile = ds["lat_percentile"].sel(gwl=gwl, year=year_index).values
    lon_percentile = ds["lon_percentile"].sel(gwl=gwl, year=year_index).values
    lat_abs_max = ds["lat_abs_max"].sel(gwl=gwl, year=year_index).values
    lon_abs_max = ds["lon_abs_max"].sel(gwl=gwl, year=year_index).values

    # Create a HoloViews dataset for visualization
    gv_data = gv.Dataset(
        (ds["projection_x_coordinate"].values, ds["projection_y_coordinate"].values, humidex_field),
        kdims=["Longitude", "Latitude"],
        vdims=["Humidex"],
    )
    quadmesh = gv_data.to(gv.QuadMesh, ["Longitude", "Latitude"], "Humidex").opts(
        cmap="RdBu_r",
        colorbar=True,
        color_levels=20,
        clim=(20, 50),
        tools=["hover"],
        width=800,
        height=600,
        xlabel="Longitude",
        ylabel="Latitude",
        title=f"GWL {gwl}, Year: {year}",
    )

    # Add location markers
    points_data = [
        (lon_percentile, lat_percentile, "99.9th Percentile", "cyan"),
        (lon_abs_max, lat_abs_max, "Absolute Max", "black"),
    ]
    markers = gv.Points(points_data, kdims=["Longitude", "Latitude"], vdims=["Description", "Color"]).opts(
        size=10,
        marker="x",
        color="Color",
        show_legend=True,
    )

    # Caption for the plot
    caption = (
        f"GWL {gwl}, Year: {year}\n\n"
        f"99.9th Percentile Max: {humidex_field.max().values:.2f}°C\n"
        f"Absolute Max: {humidex_field.max().values:.2f}°C\n"
        f"99.9th Percentile Location: ({lat_percentile:.2f}, {lon_percentile:.2f})\n"
        f"Absolute Max Location: ({lat_abs_max:.2f}, {lon_abs_max:.2f})"
    )
    st.text(caption)

    # Display the interactive plot
    st.bokeh_chart(hv.render(quadmesh * markers, backend="bokeh"), use_container_width=True)

except Exception as e:
    st.error(f"An error occurred: {e}")
