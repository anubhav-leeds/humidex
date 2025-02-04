import streamlit as st
import xarray as xr
import holoviews as hv
from holoviews import opts
import geoviews as gv
from cartopy import crs as ccrs

# Enable Holoviews for Bokeh backend
hv.extension("bokeh")

# Load the NetCDF file
@st.cache
def load_data(file_path):
    return xr.open_dataset(file_path)

# File path (Update to your correct NetCDF path)
file_path = "all_gwl_humidex_max_with_dates.nc"

# Load dataset
ds = load_data(file_path)

# Define actual GWL-specific year ranges
year_ranges = {
    "1.0": (1995, 2014),
    "1.5": (2008, 2027),
    "2.0": (2018, 2037),
    "2.5": (2029, 2048),
    "3.0": (2037, 2056),
    "4.0": (2052, 2071),
}

# Sidebar for GWL selection
st.sidebar.title("Controls")
gwl = st.sidebar.selectbox("Select GWL", list(year_ranges.keys()), index=5)  # Default: GWL 4.0

# Dynamically adjust year slider range based on selected GWL
start_year, end_year = year_ranges[gwl]
year = st.sidebar.slider("Select Year", start_year, end_year, start_year)

# Convert selected year to relative index (0–19)
relative_year = year - start_year

# Ensure relative_year is within the valid range
if relative_year < 0 or relative_year > 19:
    st.error(f"Year {year} is out of range for GWL {gwl}. Valid years: {start_year}–{start_year+19}")
    st.stop()

# Extract data for selected GWL and year
humidex_field = ds["humidex_max"].sel(gwl=gwl, year=relative_year)
lat_percentile = ds["lat_percentile"].sel(gwl=gwl, year=relative_year).values
lon_percentile = ds["lon_percentile"].sel(gwl=gwl, year=relative_year).values
lat_abs_max = ds["lat_abs_max"].sel(gwl=gwl, year=relative_year).values
lon_abs_max = ds["lon_abs_max"].sel(gwl=gwl, year=relative_year).values
date = ds["date_of_max_percentile"].sel(gwl=gwl, year=relative_year).values
absolute_max_value = humidex_field.max().values
percentile_max_value = float(humidex_field.quantile(0.999, skipna=True).values)

# Create a GeoViews dataset
gv_data = gv.Dataset(
    (ds["longitude"], ds["latitude"], humidex_field),
    kdims=["Longitude", "Latitude"],
    vdims=["Humidex"],
    crs=ccrs.PlateCarree(),
)

# Generate the interactive plot
plot = gv_data.to(gv.QuadMesh, ["Longitude", "Latitude"], ["Humidex"]).opts(
    cmap="RdBu_r",
    colorbar=True,
    clim=(20, 50),  # Fixed color bar range
    tools=["hover"],
    projection=ccrs.PlateCarree(),
    width=800,
    height=600,
    title=f"GWL {gwl}, Year: {year}, Date: {date}",
)

# Add markers for 99.9th percentile and absolute max
markers = gv.Points(
    [(lon_percentile, lat_percentile), (lon_abs_max, lat_abs_max)],
    vdims=["Location"],
    crs=ccrs.PlateCarree(),
).opts(size=10, color="black", marker="x")

# Display the interactive plot in Streamlit
st.bokeh_chart(hv.render(plot * markers, backend="bokeh"))

# Display additional information
st.markdown(
    f"""
    **Summary for GWL {gwl}, Year {year}**  
    - **Date of Maximum Humidex**: {date}  
    - **99.9th Percentile Maximum Humidex**: {percentile_max_value:.2f}°C  
    - **Absolute Maximum Humidex**: {absolute_max_value:.2f}°C  
    - **99.9th Percentile Location**: ({lat_percentile:.2f}, {lon_percentile:.2f})  
    - **Absolute Maximum Location**: ({lat_abs_max:.2f}, {lon_abs_max:.2f})  
    """
)

