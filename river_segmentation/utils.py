from affine import Affine
import numpy
from geopandas.geodataframe import GeoDataFrame
from shapely.geometry import Polygon
from shapely.ops import unary_union
from rasterio.io import DatasetReader
from rasterstats import zonal_stats
from typing import Tuple


def get_water_rgb_array_from_transect_df(
    rgb: DatasetReader, transect_polygon_df: GeoDataFrame
) -> Tuple[numpy.ndarray, Affine, GeoDataFrame, GeoDataFrame]:
    """
    Extract and crop RGB image data based on transects defined in a GeoDataFrame.

    This function reads an RGB image and a DataFrame containing transect polygons. It determines
    which transect polygons intersect with the bounds of the RGB image and then crops the image
    to the union of these intersecting transects. The function returns the cropped RGB image array,
    the affine transform for the cropped image, the subset of transect polygons within the image,
    and the updated DataFrame indicating which transects were within the RGB image bounds.

    Parameters:
    -----------
    rgb : rasterio.io.DatasetReader
        A rasterio dataset reader object representing the RGB image.
    transect_polygon_df : geopandas.geodataframe.GeoDataFrame
        A DataFrame containing transect polygons, with a "geometry" column holding shapely Polygon objects.

    Returns:
    --------
    water_rgb_array : numpy.ndarray
        A 3D numpy array of the cropped RGB image data, with shape (height, width, 3).
    affine_transform : affine.Affine
        The affine transform for the cropped RGB image.
    transect_polygon_in_rgb : geopandas.geodataframe.GeoDataFrame
        A DataFrame of transect polygons that intersect with the RGB image bounds.
    transect_polygon_df : geopandas.geodataframe.GeoDataFrame
        The original DataFrame with an additional column "is_in_rgb" indicating which transects
        are within the RGB image bounds.
    """
    rgb_bounds = rgb.bounds
    rgb_polygon = Polygon(
        [
            (rgb_bounds.left, rgb_bounds.top),
            (rgb_bounds.left, rgb_bounds.bottom),
            (rgb_bounds.right, rgb_bounds.bottom),
            (rgb_bounds.right, rgb_bounds.top),
            (rgb_bounds.left, rgb_bounds.top),
        ]
    )
    rgb_array = rgb.read()
    rgb_array = rgb_array[:3, :, :].transpose(1, 2, 0)
    is_in_rgb_list = []
    for _, row in transect_polygon_df.iterrows():
        specific_transect_polygon = row["geometry"]
        is_in_rgb = specific_transect_polygon.within(rgb_polygon)
        if is_in_rgb is True:
            transect_stats = zonal_stats(
                row["geometry"],
                rgb_array[:, :, 0],
                affine=rgb.transform,
                nodata=None,
                stats=["min", "max"],
            )[0]
            if (transect_stats["min"] == 0) or (transect_stats["max"] == 255):
                is_in_rgb = False
        is_in_rgb_list.append(is_in_rgb)
    transect_polygon_df["is_in_rgb"] = is_in_rgb_list

    transect_polygon_in_rgb = transect_polygon_df[
        transect_polygon_df["is_in_rgb"]
    ].reset_index(drop=True)
    polygon_list = transect_polygon_in_rgb["geometry"].to_list()
    all_transect_polygon = unary_union(polygon_list)
    return all_transect_polygon


def find_bounding_box(image: numpy.ndarray) -> Tuple[int, int, int, int]:
    """
    Find the bounding box of non-zero pixels in an image.

    This function identifies the smallest rectangular bounding box that contains all
    non-zero pixels in a given image. The image is expected to have multiple bands,
    and the function considers pixels as non-zero if any of the first three bands
    have a non-zero value.

    Parameters:
    -----------
    image : numpy.ndarray
        A 3D numpy array representing the image, with shape (bands, height, width).
        The function assumes the first three bands are used to determine non-zero pixels.

    Returns:
    --------
    xmin : int
        The minimum x-coordinate (column) of the bounding box.
    xmax : int
        The maximum x-coordinate (column) of the bounding box.
    ymin : int
        The minimum y-coordinate (row) of the bounding box.
    ymax : int
        The maximum y-coordinate (row) of the bounding box.
    """
    # Collapse the bands by checking for non-zero pixels across all bands
    non_zero_pixels = numpy.any(image[:3] != 0, axis=0)
    non_nan_pixels = ~numpy.any(numpy.isnan(image[:3]), axis=0)
    non_zero_pixels = non_zero_pixels * non_nan_pixels

    # Find rows and columns with any non-zero pixels
    non_zero_rows = numpy.any(non_zero_pixels, axis=1)
    non_zero_cols = numpy.any(non_zero_pixels, axis=0)

    # Identify the indices of the non-zero rows and columns
    ymin, ymax = numpy.where(non_zero_rows)[0][[0, -1]]
    xmin, xmax = numpy.where(non_zero_cols)[0][[0, -1]]
    return xmin, xmax, ymin, ymax
