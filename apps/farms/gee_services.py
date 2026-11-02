import threading
from datetime import date, timedelta
from pathlib import Path

import ee
import pandas as pd
from django.conf import settings

# ============================================================
# CONFIGURATION
# ============================================================

DAYS_BACK = 30
MAX_CLOUD_PCT = 80
LANDSAT_MAX_CLOUD_PCT = 60
POINT_BUFFER_M = 100

SENTINEL_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"

LANDSAT_COLLECTIONS = [
    "LANDSAT/LC08/C02/T1_L2",
    "LANDSAT/LC09/C02/T1_L2",
]

# Earth Engine initialization is cached per worker process.
_ee_initialized = False
_ee_lock = threading.Lock()


# ============================================================
# EARTH ENGINE AUTHENTICATION
# ============================================================


def initialize_earth_engine():
    global _ee_initialized

    if _ee_initialized:
        return ee

    with _ee_lock:
        if _ee_initialized:
            return ee

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

        _ee_initialized = True

    return ee


# ============================================================
# BOUNDARY CONVERSION
# ============================================================


def boundary_to_ee(boundary, point_buffer=POINT_BUFFER_M):
    """
    Convert farm boundary coordinates into Earth Engine geometry.

    Input coordinate format:
        [[latitude, longitude], ...]

    Earth Engine coordinate format:
        [longitude, latitude]

    Supports:
        - Single coordinate pair: [lat, lng]
        - Point list: [[lat, lng]]
        - Polygon: [[lat, lng], [lat, lng], ...]
    """

    if not isinstance(boundary, (list, tuple)) or not boundary:
        raise ValueError("Boundary must be a non-empty list.")

    # Single point: [latitude, longitude]
    if len(boundary) == 2 and all(isinstance(x, (int, float)) for x in boundary):
        lat, lng = boundary

        _validate_coordinate(lat, lng)

        return ee.Geometry.Point([lng, lat]).buffer(point_buffer)

    # Validate coordinate pairs.
    coordinates = []

    for point in boundary:

        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError(f"Invalid coordinate pair: {point}")

        lat, lng = point

        _validate_coordinate(lat, lng)

        coordinates.append([lng, lat])

    if len(coordinates) == 1:
        return ee.Geometry.Point(coordinates[0]).buffer(point_buffer)

    if len(coordinates) < 3:
        raise ValueError("A polygon requires at least 3 coordinate pairs.")

    # Close polygon ring.
    if coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0])

    return ee.Geometry.Polygon([coordinates])


def _validate_coordinate(lat, lng):
    if not isinstance(lat, (int, float)):
        raise ValueError("Latitude must be numeric.")

    if not isinstance(lng, (int, float)):
        raise ValueError("Longitude must be numeric.")

    if not -90 <= lat <= 90:
        raise ValueError(f"Invalid latitude: {lat}")

    if not -180 <= lng <= 180:
        raise ValueError(f"Invalid longitude: {lng}")


def mask_s2_clouds(img):
    """
    Mask clouds, cloud shadows, cirrus, snow,
    saturated pixels and no-data pixels using SCL.
    """

    scl = img.select("SCL")

    bad_pixels = (
        scl.eq(0)  # No data
        .Or(scl.eq(1))  # Saturated / defective
        .Or(scl.eq(3))  # Cloud shadow
        .Or(scl.eq(8))  # Medium probability cloud
        .Or(scl.eq(9))  # High probability cloud
        .Or(scl.eq(10))  # Cirrus
        .Or(scl.eq(11))  # Snow / ice
    )

    return img.updateMask(bad_pixels.Not())


def add_indices(img):
    """
    Calculate vegetation and water indices.

    Source:
        Sentinel-2 Surface Reflectance Harmonized.

    Reflectance is scaled from 0-10000 to 0-1.
    """

    bands = [
        "B2",
        "B3",
        "B4",
        "B5",
        "B7",
        "B8",
        "B11",
    ]

    s = img.select(bands).divide(10000)

    # Normalized Difference Vegetation Index
    ndvi = s.normalizedDifference(["B8", "B4"]).rename("ndvi")

    # Enhanced Vegetation Index
    evi = s.expression(
        "2.5 * ((NIR - RED) / " "(NIR + 6 * RED - 7.5 * BLUE + 1))",
        {
            "NIR": s.select("B8"),
            "RED": s.select("B4"),
            "BLUE": s.select("B2"),
        },
    ).rename("evi")

    # Normalized Difference Water Index
    ndwi = s.normalizedDifference(["B3", "B8"]).rename("ndwi")

    # Land Surface Water Index
    lswi = s.normalizedDifference(["B8", "B11"]).rename("lswi")

    # Normalized Difference Red Edge
    ndre = s.normalizedDifference(["B8", "B5"]).rename("ndre")

    # Chlorophyll Index Red Edge
    ci_rededge = s.expression(
        "(B7 / B5) - 1",
        {
            "B7": s.select("B7"),
            "B5": s.select("B5"),
        },
    ).rename("ci_rededge")

    result = ee.Image.cat(
        [
            ndvi,
            evi,
            ndwi,
            lswi,
            ndre,
            ci_rededge,
        ]
    )

    return result.copyProperties(
        img,
        ["system:time_start"],
    )


def feature_collection_to_dataframe(collection, value_column):
    """
    Convert an Earth Engine FeatureCollection into Pandas DataFrame.
    """

    features = collection.getInfo().get("features", [])

    if not features:
        return pd.DataFrame()

    records = [feature.get("properties", {}) for feature in features]

    df = pd.DataFrame(records)

    if df.empty or "date" not in df.columns:
        return pd.DataFrame()

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    df = df.dropna(subset=["date"])

    if value_column not in df.columns:
        return pd.DataFrame()

    df[value_column] = pd.to_numeric(
        df[value_column],
        errors="coerce",
    )

    df = df.dropna(subset=[value_column])

    return df.groupby("date", as_index=False).mean(numeric_only=True).sort_values("date")


def fetch_sentinel2(geometry, start, end, max_cloud):
    """
    Fetch Sentinel-2 imagery and calculate vegetation indices.

    Returns:
        Pandas DataFrame
    """

    collection = (
        ee.ImageCollection(SENTINEL_COLLECTION)
        .filterBounds(geometry)
        .filterDate(start, end)
        .filter(
            ee.Filter.lt(
                "CLOUDY_PIXEL_PERCENTAGE",
                max_cloud,
            )
        )
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

        return ee.Feature(
            None,
            stats,
        ).set(
            "date",
            img.date().format("YYYY-MM-dd"),
        )

    features = ee.FeatureCollection(collection.map(to_feature))

    df = feature_collection_to_dataframe(
        features,
        "ndvi",
    )

    return df


def fetch_landsat_lst(geometry, start, end):
    """
    Calculate Land Surface Temperature in Celsius.

    Source:
        Landsat 8 and Landsat 9 Collection 2 Level 2.

    ST_B10 conversion:
        Kelvin = DN * 0.00341802 + 149.0
        Celsius = Kelvin - 273.15
    """

    def prepare_landsat(img):

        qa = img.select("QA_PIXEL")

        # Remove fill, dilated cloud, cirrus, cloud,
        # cloud shadow and snow pixels.
        bad_bits = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3) | (1 << 4) | (1 << 5)

        clear_mask = qa.bitwiseAnd(bad_bits).eq(0)

        saturation_mask = img.select("QA_RADSAT").eq(0)

        lst = img.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15).rename("lst")

        return (
            lst.updateMask(clear_mask)
            .updateMask(saturation_mask)
            .copyProperties(
                img,
                ["system:time_start"],
            )
        )

    collection = (
        ee.ImageCollection(LANDSAT_COLLECTIONS[0])
        .merge(ee.ImageCollection(LANDSAT_COLLECTIONS[1]))
        .filterBounds(geometry)
        .filterDate(start, end)
        .filter(
            ee.Filter.lt(
                "CLOUD_COVER",
                LANDSAT_MAX_CLOUD_PCT,
            )
        )
        .map(prepare_landsat)
    )

    def to_feature(img):

        stats = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=30,
            maxPixels=1e9,
            bestEffort=True,
        )

        return ee.Feature(
            None,
            stats,
        ).set(
            "date",
            img.date().format("YYYY-MM-dd"),
        )

    features = ee.FeatureCollection(collection.map(to_feature))

    return feature_collection_to_dataframe(
        features,
        "lst",
    )


def get_date_range(days_back=DAYS_BACK, target_date=None):
    """
    Generate an Earth Engine date range.

    If target_date is supplied, include that entire calendar day
    and the preceding days_back days.

    Earth Engine filterDate uses an exclusive end date.
    """

    if isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)

    if target_date is None:
        end_date = date.today()
    else:
        end_date = target_date

    start_date = end_date - timedelta(days=days_back)

    exclusive_end = end_date + timedelta(days=1)

    return (
        start_date.isoformat(),
        exclusive_end.isoformat(),
    )


def fetch_gee_data(
    boundary,
    target_date=None,
    days_back=DAYS_BACK,
):

    # Initialize before using any Earth Engine objects.
    initialize_earth_engine()

    if days_back < 0:
        raise ValueError("days_back cannot be negative.")

    geometry = boundary_to_ee(
        boundary,
        POINT_BUFFER_M,
    )

    start, end = get_date_range(
        days_back=days_back,
        target_date=target_date,
    )

    # Fetch Sentinel-2 vegetation indices.
    s2_df = fetch_sentinel2(
        geometry,
        start,
        end,
        MAX_CLOUD_PCT,
    )

    if s2_df.empty:
        raise ValueError(
            "No usable Sentinel-2 observations found. " "Try increasing days_back or adjusting cloud filtering."
        )

    # Fetch Landsat temperature observations.
    lst_df = fetch_landsat_lst(
        geometry,
        start,
        end,
    )

    # Merge nearest Landsat observation with Sentinel-2.
    s2_df = s2_df.sort_values("date")

    if not lst_df.empty:

        lst_df = lst_df.sort_values("date")

        df = pd.merge_asof(
            s2_df,
            lst_df[["date", "lst"]],
            on="date",
            direction="nearest",
            tolerance=pd.Timedelta(days=8),
        )

    else:
        df = s2_df.copy()
        df["lst"] = float("nan")

    if df.empty:
        raise ValueError("No usable satellite observations found.")

    # Select latest Sentinel-2 observation.
    latest = df.iloc[-1]

    result = {
        "recorded_at": latest["date"].date().isoformat(),
        "ci_rededge": _safe_float(latest["ci_rededge"]),
        "evi": _safe_float(latest["evi"]),
        "lswi": _safe_float(latest["lswi"]),
        "ndre": _safe_float(latest["ndre"]),
        "ndvi": _safe_float(latest["ndvi"]),
        "ndwi": _safe_float(latest["ndwi"]),
        "lst": _safe_float(latest["lst"]),
    }

    return result


def _safe_float(value):
    """
    Convert Pandas / NumPy values into JSON-compatible floats.
    Missing values become None.
    """

    if pd.isna(value):
        return None

    return float(value)
