import streamlit as st
import xarray as xr
import holoviews as hv
import geoviews as gv
from cartopy import crs as ccrs

hv.extension("bokeh")

# Load the NetCDF file
FILE_PATH = "all_gwl_humidex_max_with_dates.nc"
ds = xr.open_dataset(FILE_PATH)

# Streamlit App
st.title("Interactive Humidex Viewer")

# Sidebar Controls
gwl_selector = st.sidebar.selectbox("Select GWL", options=ds.gwl.values, index=0)
year_selector = st.sidebar.selectbox(
    "Select Year",
    options=ds.year.values,
    index=0,
    format_func=lambda y: f"{y}",
)

# Extract data for the selected GWL and Year
gwl = gwl_selector
year = year_selector

try:
    # Validate year and GWL selection
    humidex_field = ds["humidex_max"].sel(gwl=gwl, year=year)
    lat_percentile = ds["lat_percentile"].sel(gwl=gwl, year=year).values
    lon_percentile = ds["lon_percentile"].sel(gwl=gwl, year=year).values
    lat_abs_max = ds["lat_abs_max"].sel(gwl=gwl, year=year).values
    lon_abs_max = ds["lon_abs_max"].sel(gwl=gwl, year=year).values

    latitude = ds["latitude"]
    longitude = ds["longitude"]

    # Debugging: Confirm data shapes
    st.write(f"Humidex Field Shape: {humidex_field.shape}")
    st.write(f"Selected Year: {year}, GWL: {gwl}")
    st.write(f"99.9th Percentile Location: {lat_percentile}, {lon_percentile}")
    st.write(f"Absolute Max Location: {lat_abs_max}, {lon_abs_max}")

    # Create a GeoViews plot
    gv_data = gv.Dataset(
        (longitude, latitude, humidex_field),
        kdims=["Longitude", "Latitude"],
        vdims=["Humidex"],
        crs=ccrs.PlateCarree(),
    )

    quadmesh = gv_data.to(
        gv.QuadMesh, kdims=["Longitude", "Latitude"], vdims="Humidex"
    ).opts(
        cmap="RdBu_r",
        colorbar=True,
        colorbar_opts={"label_standoff": 10, "extend": "both"},
        clim=(20, 50),  # Fixed range with open-ended bounds
        tools=["hover"],
        width=800,
        height=600,
        projection=ccrs.PlateCarree(),
        xlabel="Longitude",
        ylabel="Latitude",
    )

    # Add location markers
    markers = gv.Points(
        [
            (lon_percentile, lat_percentile, "99.9th Percentile", "cyan"),
            (lon_abs_max, lat_abs_max, "Absolute Max", "black"),
        ],
        kdims=["Longitude", "Latitude"],
        vdims=["Description", "Color"],
        crs=ccrs.PlateCarree(),
    ).opts(
        size=10,
        color="Color",
        marker="x",
        show_legend=True,
    )

    # Add caption
    caption = f"""
    **GWL {gwl}, Year: {year}**
    - 99.9th Percentile Max: {humidex_field.max().values:.2f}°C
    - Absolute Max: {humidex_field.max().values:.2f}°C
    - 99.9th Percentile Location: ({lat_percentile:.2f}, {lon_percentile:.2f})
    - Absolute Max Location: ({lat_abs_max:.2f}, {lon_abs_max:.2f})
    """
    st.markdown(caption)

    # Render the plot
    st.bokeh_chart(hv.render(quadmesh * markers, backend="bokeh"), use_container_width=True)

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.stop()
