import panel as pn
import xarray as xr
import geoviews as gv
import holoviews as hv
from holoviews import opts
from cartopy import crs as ccrs

# Load Panel extension
pn.extension()

# Load the NetCDF file
nc_file_path = "all_gwl_humidex_max_with_dates.nc"
ds = xr.open_dataset(nc_file_path)

# Define GWL-specific year ranges
year_ranges = {
    "1.0": (1995, 2014),
    "1.5": (2008, 2027),
    "2.0": (2018, 2037),
    "2.5": (2029, 2048),
    "3.0": (2037, 2056),
    "4.0": (2052, 2071),
}

# Interactive widgets
gwl_selector = pn.widgets.Select(name="Select GWL", options=list(year_ranges.keys()), value="4.0")
year_selector = pn.widgets.IntSlider(name="Select Year", start=2052, end=2071, step=1, value=2052)

# Update year slider dynamically
@pn.depends(gwl_selector.param.value, watch=True)
def update_year_slider(gwl):
    start_year, end_year = year_ranges[gwl]
    year_selector.start = start_year
    year_selector.end = end_year
    year_selector.value = start_year

# Plot function
@pn.depends(gwl_selector.param.value, year_selector.param.value)
def plot_humidex(gwl, year):
    start_year = year_ranges[gwl][0]
    relative_year = year - start_year
    
    # Extract data
    humidex_field = ds["humidex_max"].sel(gwl=gwl, year=relative_year)
    lat_percentile = ds["lat_percentile"].sel(gwl=gwl, year=relative_year).values
    lon_percentile = ds["lon_percentile"].sel(gwl=gwl, year=relative_year).values
    lat_abs_max = ds["lat_abs_max"].sel(gwl=gwl, year=relative_year).values
    lon_abs_max = ds["lon_abs_max"].sel(gwl=gwl, year=relative_year).values
    date = ds["date_of_max_percentile"].sel(gwl=gwl, year=relative_year).values
    absolute_max_value = humidex_field.max().values
    percentile_max_value = float(humidex_field.quantile(0.999, skipna=True).values)

    # Convert to GeoViews dataset
    gv_data = gv.Dataset(
        (ds["longitude"], ds["latitude"], humidex_field),
        kdims=["Longitude", "Latitude"],
        vdims=["Humidex"],
        crs=ccrs.PlateCarree(),
    )
    
    # Create QuadMesh
    quadmesh = gv_data.to(gv.QuadMesh, ["Longitude", "Latitude"], ["Humidex"]).opts(
        cmap="RdBu_r",
        colorbar=True,
        clim=(20, 50),
        projection=ccrs.PlateCarree(),
        width=800,
        height=600,
        title=f"GWL {gwl}, Date: {date}",
    )

    # Add markers
    markers = gv.Points(
        [(lon_percentile, lat_percentile, "99.9th Percentile", "cyan"),
         (lon_abs_max, lat_abs_max, "Absolute Max", "black")],
        vdims=["Description", "Color"],
        crs=ccrs.PlateCarree(),
    ).opts(size=10, marker="x", color="Color", show_legend=True)
    
    return quadmesh * markers

# Panel layout
layout = pn.Column(
    "# Interactive Humidex Plot",
    gwl_selector,
    year_selector,
    plot_humidex,
)

# Serve the app
update_year_slider(gwl_selector.value)
layout.servable()
