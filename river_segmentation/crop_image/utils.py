import numpy
import rasterio
from rasterio.features import shapes, geometry_mask
from rasterio.enums import Resampling
from shapely.geometry import Polygon


def get_bounding_polygon_of_image(image_array, transform):
    valid_mask = image_array != 0
    shapes_generator = shapes(valid_mask.astype(numpy.uint8), transform=transform)
    polygons = [
        Polygon(geometry["coordinates"][0])
        for geometry, value in shapes_generator
        if value == 1
    ]
    bigest_polygon_index = numpy.argmax([polygon.area for polygon in polygons])
    polygon = polygons[bigest_polygon_index]
    return polygon


def crop_image_under_from_2_images(image_under_path, image_over_path, do_ovr=True):
    image_under = rasterio.open(image_under_path)
    image_over = rasterio.open(image_over_path)
    image_under_array = image_under.read()
    image_over_array = image_over.read()
    image_under_polygon = get_bounding_polygon_of_image(
        image_under_array[0, :, :], image_under.transform
    )
    image_over_polygon = get_bounding_polygon_of_image(
        image_over_array[0, :, :], image_over.transform
    )
    image_under_good_polygon = image_under_polygon.difference(image_over_polygon)
    image_under_good_mask = geometry_mask(
        [image_under_good_polygon],
        out_shape=image_under.shape,
        transform=image_under.transform,
    )
    image_under.close()
    image_over.close()
    with rasterio.open(image_under_path, "r+") as dataset:
        data = dataset.read()  # Read all bands (shape: (bands, rows, cols))

        # Step 2: Apply the mask
        # Assume mask is a 2D array of the same shape as one band (rows, cols)
        # Broadcast mask to all bands if necessary
        data[:, image_under_good_mask] = 0  # Set masked pixels to 0

        dataset.nodata = 0

        # Step 3: Write the modified data back
        dataset.write(data)

        if do_ovr:
            # Step 4: Rebuild the overviews for the .tif.ovr file
            overview_levels = [2, 4, 8, 16]  # Define reduction levels
            dataset.build_overviews(overview_levels, Resampling.nearest)
            dataset.update_tags(ns="rio_overview", resampling="nearest")
