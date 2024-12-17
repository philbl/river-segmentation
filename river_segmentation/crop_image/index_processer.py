import os
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio as rio
from shapely.geometry import box


class IndexProcesser:
    def __init__(self):
        self._index_path = None
        self._index_original = None
        self._trimmed_index = None
        self._photos_path = None
        self._raster_box_index = None
        pass

    @property
    def photos(self):
        return self._photos_path

    @photos.setter
    def photos(self, path: str) -> str:
        self._photos_path = path

    @property
    def trimmed_index(self) -> gpd.GeoDataFrame:
        return self._trimmed_index

    @trimmed_index.setter
    def trimmed_index(self, gdf: gpd.GeoDataFrame):
        self._trimmed_index = gdf

    @property
    def index(self) -> gpd.GeoDataFrame:
        return self._index_original

    @index.setter
    def index(self, index_path: str):
        self._index_path = index_path
        self._index_original = gpd.read_file(index_path)

    @property
    def raster_box_index(self) -> gpd.GeoDataFrame:
        return self._raster_box_index 
    
    @raster_box_index.setter
    def raster_box_index(self, gdf: gpd.GeoDataFrame):
        self._raster_box_index = gdf
    
    @classmethod
    def get_neighbours(cls, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        # https://gis.stackexchange.com/questions/281652/finding-all-neighbors-using-geopandas
        # Drop the column if it exist
        if 'NEIGHBORS' in gdf.columns:
            gdf = gdf.drop(columns=["NEIGHBORS", "KEEP"])
        # add NEIGHBORS column
        gdf = gdf.reindex(columns=gdf.columns.tolist() + ['NEIGH', 'NEIGH_INDEX'])
        gdf["NEIGH"] = ''
        gdf["NEIGH_INDEX"] = ''
        for index, feature in gdf.iterrows():
            # get 'not disjoint' countries
            neighbors = gdf[~gdf.geometry.disjoint(feature.geometry)]["NOM_IMAGE_"].tolist()
            neighbors_index = gdf[~gdf.geometry.disjoint(feature.geometry)].index.tolist()
            neighbors = [name for name in neighbors if feature["NOM_IMAGE_"] != name]
            neighbors_index = [ind for ind in neighbors_index if feature["ind"] != ind]
            # except ValueError:
            if isinstance(neighbors, list):
                gdf.at[index, "NEIGH"] = str(neighbors)
                gdf.at[index, "NEIGH_INDEX"] = str(neighbors_index)
            else:
                gdf.at[index, "NEIGHBORS"] = str(list([int(neighbors)]))
                gdf.at[index, "NEIGH_INDEX"] = str(list([int(neighbors_index)]))
        return gdf
    
    @classmethod
    def get_image_name(cls, gdf: gpd.GeoDataFrame) -> list:
        gdf.index = [i for i in range(len(gdf))]
        # Names
        name_list = gdf["NOM_IMAGE_"].values
        names_compararison = []
        for name in name_list:
            name_split = name.split("_")
            name_split.pop()
            name_numbered = "_".join(name_split)
            names_compararison.append(name_numbered)
        # name_list = []
        return names_compararison

    def reproject_index(self, objtecive_crs: str):
        self._index_original = self._index_original.to_crs(epsg=objtecive_crs)
        # return 0

    def trim_index(self):
        # Check that the name exist
        try:
            gdf = self.index.sort_values(by=["DATE_PHOTO"])
        except Exception as exc:
            raise ValueError("The name DATE_PHOTO does not exist in your dataset.") from exc
        # Get unique values
        names = self.get_image_name(gdf)
        gdf["names_short"] = names
        gdf = gdf.drop_duplicates(subset=['names_short'])
        gdf["ind"] = [i for i in range(len(gdf))]
        gdf.index = [i for i in range(len(gdf))]
        gdf = self.get_neighbours(gdf)
        self.trimmed_index = gdf
        return 0

    def create_box_from_extent(self, ext_prefix: str):
        modified_gdf = self.trimmed_index.copy()
        # with rio.open(raster_path) as src:
        for idx, feature in self.trimmed_index.iterrows():
            # Get the name of the current feature
            try:
                self.index.sort_values(by=["NOM_IMAGE_"])
            except Exception as exc:
                raise ValueError("The name NOM_IMAGE_ does not exist in your dataset.") from exc
            
            raster_name = feature["NOM_IMAGE_"]
            raster_name = raster_name.split("_")
            raster_name.pop()
            raster_name = "_".join(raster_name) + f"_{ext_prefix}.tif"
            # Open the associated raster
            raster_path = os.path.join(self.photos, raster_name)
            with rio.open(raster_path) as src:
                bounds = src.bounds
                geom = box(*bounds)
                modified_gdf.loc[idx, "geometry"] = geom
        shp_path = os.path.split(raster_path)
        modified_gdf.to_file(os.path.join(shp_path[0],"Index\RasterBox_Index.shp"))
        self.raster_box_index = modified_gdf
        return 0

    def clip_overlapping_features(self):
        # Load the shapefile
        gdf = self.raster_box_index
        # Ensure geometries are valid
        gdf['geometry'] = gdf['geometry'].buffer(0)  # Fix invalid geometries if necessary
        # Create a copy of the GeoDataFrame to modify
        modified_gdf = gdf.copy()
        # Loop through each feature
        for idx, feature in gdf.iterrows():
            current_geom = feature.geometry
            for other_idx, other_feature in modified_gdf.iterrows():
                if idx >= other_idx:  # Skip self and previous features
                    continue
                other_geom = other_feature.geometry
                # Check if geometries intersect
                if current_geom.intersects(other_geom):
                    # Debugging
                    # print(f"Feature {idx} intersects with Feature {other_idx}")
                    # Clip the intersecting part from the other geometry
                    difference = other_geom.difference(current_geom)

                    # Update the other feature's geometry
                    modified_gdf.at[other_idx, 'geometry'] = difference

        # Export the index create by raster extent
        save_path = os.path.split(self._index_path)
        modified_gdf.to_file(os.path.join(save_path[0],"Clipped_RasterBox_Index.shp"))