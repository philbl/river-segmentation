import rasterio
from rasterio.windows import Window
from rasterio.features import geometry_mask
import numpy
import geopandas
from skimage import img_as_float32

from river_segmentation.utils import (
    get_water_rgb_array_from_transect_df,
    find_bounding_box,
)


class ImageHandler:
    def __init__(self, image_path, transect_path):
        self.image_path = image_path
        self.transect_path = transect_path
        self.rgbnir = self._load_raster(self.image_path, self.transect_path)
        self.ndvi = self._load_ndvi()
        self.nir = self._load_nir()
        self.image_shape = self.rgbnir.shape[:2]

    def _load_raster(self, image_path, transect_path):
        transect_polygon_df = geopandas.read_file(transect_path)
        with rasterio.open(image_path) as src:
            all_transect_polygon = get_water_rgb_array_from_transect_df(
                src, transect_polygon_df
            )
            river_mask = geometry_mask(
                all_transect_polygon.geoms,
                out_shape=src.shape,
                transform=src.transform,
                invert=True,
            )
            xmin, xmax, ymin, ymax = find_bounding_box(
                numpy.atleast_3d(river_mask).transpose(2, 0, 1)
            )
            window = Window(
                row_off=ymin,
                col_off=xmin,
                width=xmax - xmin + 1,
                height=ymax - ymin + 1,
            )
            img_array = src.read(window=window)

        rgbnir_array = img_array.transpose(1, 2, 0)
        # subset = rgbnir_array[ymin:ymax, xmin:xmax]
        return rgbnir_array

    def _load_nir(self):
        return self.rgbnir[:, :, 3]

    def _load_ndvi(self):
        subset_image = self.rgbnir
        subset_float = img_as_float32(subset_image)
        ndvi = (subset_float[:, :, 3] - subset_float[:, :, 0]) / (
            subset_float[:, :, 3] + subset_float[:, :, 0]
        )
        ndvi[numpy.isnan(ndvi)] = -999
        ndvi = ndvi.round(4)
        return ndvi
