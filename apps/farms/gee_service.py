from datetime import date, timedelta
from pathlib import Path

import ee
import pandas as pd
from django.conf import settings

SERVICE_ACCOUNT = settings.SERVICE_ACCOUNT
KEY_FILE = settings.KEY_FILE
PROJECT_ID = settings.PROJECT_ID

DAYS_BACK = 1  # how far back to look
MAX_CLOUD_PCT = 80  # scene-level cloud filter
POINT_BUFFER_M = 100


def initialize_earth_engine():
    key_file = Path(settings.KEY_FILE).expanduser()

    if not key_file.is_file():
        raise FileNotFoundError(f"Earth Engine key file not found: {key_file}")

    credentials = ee.ServiceAccountCredentials(
        settings.SERVICE_ACCOUNT,
        str(key_file),
    )

    ee.Initialize(
        credentials=credentials,
        project=settings.PROJECT_ID,
    )


def boundary_to_ee(boundary, point_buffer=100):
    """boundary: [[lat, lng], ...] -> ee.Geometry (Earth Engine wants [lng, lat])."""
    if not boundary or not isinstance(boundary, (list, tuple)):
        raise ValueError(f"Invalid boundary: {boundary}")

    # a flat [lat, lng] single point
    if isinstance(boundary[0], (int, float)):
        return ee.Geometry.Point([boundary[1], boundary[0]]).buffer(point_buffer)

    pts = [[p[1], p[0]] for p in boundary]  # swap to [lng, lat]
    if len(pts) == 1:
        return ee.Geometry.Point(pts[0]).buffer(point_buffer)
    if len(pts) < 3:
        raise ValueError("A polygon needs at least 3 points")
    if pts[0] != pts[-1]:
        pts.append(pts[0])  # close the ring
    return ee.Geometry.Polygon([pts])


def mask_s2_clouds(img):
    """Mask cloud, shadow and cirrus using the Scene Classification band."""
    scl = img.select("SCL")
    bad = scl.eq(3).Or(scl.eq(8)).Or(scl.eq(9)).Or(scl.eq(10)).Or(scl.eq(11))
    return img.updateMask(bad.Not())


def add_indices(img):
    """Compute spectral indices on reflectance scaled to 0-1."""
    s = img.select(["B2", "B3", "B4", "B5", "B7", "B8", "B11"]).divide(10000)
    ndvi = s.normalizedDifference(["B8", "B4"]).rename("ndvi")
    evi = s.expression(
        "2.5 * ((NIR - R) / (NIR + 6*R - 7.5*B + 1))",
        {"NIR": s.select("B8"), "R": s.select("B4"), "B": s.select("B2")},
    ).rename("evi")
    ndwi = s.normalizedDifference(["B3", "B8"]).rename("ndwi")  # McFeeters (water content of canopy/open water)
    lswi = s.normalizedDifference(["B8", "B11"]).rename("lswi")  # land surface water index
    ndre = s.normalizedDifference(["B8", "B5"]).rename("ndre")
    ci = s.expression("B7 / B5 - 1", {"B7": s.select("B7"), "B5": s.select("B5")}).rename("ci_rededge")
    out = ee.Image.cat([ndvi, evi, ndwi, lswi, ndre, ci])
    return out.copyProperties(img, ["system:time_start"])


def fetch_sentinel2(geometry, start, end, max_cloud):
    coll = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(geometry)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud))
        .map(mask_s2_clouds)
        .map(add_indices)
    )

    def to_feature(img):
        stats = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=20,
            maxPixels=1e9,
            bestEffort=True,
        )
        return ee.Feature(None, stats).set("date", img.date().format("YYYY-MM-dd"))

    feats = ee.FeatureCollection(coll.map(to_feature)).getInfo()["features"]
    df = pd.DataFrame([f["properties"] for f in feats])
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["ndvi"])
    return df.groupby("date", as_index=False).mean(numeric_only=True).sort_values("date")


def fetch_landsat_lst(geometry, start, end):
    """Land surface temperature (deg C) from Landsat 8/9 Collection 2 Level 2.
    Sentinel-2 has no thermal band, so LST must come from Landsat."""

    def prep(img):
        lst = img.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15).rename("lst")
        return lst.copyProperties(img, ["system:time_start"])

    coll = (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
        .filterBounds(geometry)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUD_COVER", 60))
        .map(prep)
    )

    def to_feature(img):
        stats = img.reduceRegion(ee.Reducer.mean(), geometry, 30, maxPixels=1e9, bestEffort=True)
        return ee.Feature(None, stats).set("date", img.date().format("YYYY-MM-dd"))

    feats = ee.FeatureCollection(coll.map(to_feature)).getInfo()["features"]
    df = pd.DataFrame([f["properties"] for f in feats])
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    return df.dropna(subset=["lst"]).groupby("date", as_index=False).mean().sort_values("date")


# Calculation
def fetch_gee_data(boundary):
    geometry = boundary_to_ee(boundary, POINT_BUFFER_M)

    end_d = date.today()
    start_d = end_d - timedelta(days=DAYS_BACK)
    start, end = start_d.isoformat(), end_d.isoformat()

    print(f"Area: {geometry.area().getInfo() / 10000:.2f} ha | {start} -> {end}")

    s2 = fetch_sentinel2(geometry, start, end, MAX_CLOUD_PCT)
    if s2.empty:
        return "No usable Sentinel-2 observations. Try a longer DAYS_BACK or a higher MAX_CLOUD_PCT."

    lst = fetch_landsat_lst(geometry, start, end)
    if not lst.empty:
        df = pd.merge_asof(s2, lst, on="date", direction="nearest", tolerance=pd.Timedelta(days=8))
    else:
        df = s2.assign(lst=None)
    ci_rededge, evi, lswi, ndre, ndvi, ndwi, lst = df.iloc[-1][
        ["ci_rededge", "evi", "lswi", "ndre", "ndvi", "ndwi", "lst"]
    ].values
    return ci_rededge, evi, lswi, ndre, ndvi, ndwi, lst
