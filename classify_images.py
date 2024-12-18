import os
import shutil
import geopandas as gpd


def get_image_name(gdf: gpd.GeoDataFrame) -> list:
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


def main():

    raster_folder = r"/folder/where/the/photos/are/saved"
    index_shp_name = r"/index/of/the/images/"
    # Output path
    out_path = r"/folder/where/you/want/to/store/the/classified/rivers"
    # list raster files:
    raster_list = os.listdir(raster_folder)
    raster_list = [i.replace(".tif", "")
                   for i in raster_list if i.endswith(".tif")]
    raster_list = [os.path.join(raster_folder, i) for i in raster_list]
    index_tiles_shp = gpd.read_file(index_shp_name)
    index_tiles_shp = index_tiles_shp.sort_values(by=["NOM_IMAGE_"])

    # Loop into each river name
    rivers_names = index_tiles_shp["Nom_Cours_"].values
    # Track image names already moved
    track_image = []
    for river_name in rivers_names:
        # Filter index by the river name
        river_index_shp = index_tiles_shp[index_tiles_shp["Nom_Cours_"] == river_name]
        names_index = get_image_name(river_index_shp)
        for raster in raster_list:
            file_name = os.path.split(raster)[-1]
            file_name_split = file_name.split("_")
            file_name_split.pop()
            if len(file_name) > 2:
                file_name_split.pop()
            name_join = "_".join(file_name_split)
            if name_join in names_index:
                output_dir = os.path.join(out_path, river_name)
                if not os.path.exists(output_dir):
                    os.mkdir(output_dir)
                if raster in track_image:
                    # print(f"{raster} already tracked")
                    continue
                shutil.move(raster+".tif",
                            os.path.join(output_dir, file_name+".tif"))
                shutil.move(raster+".tif.aux.xml",
                            os.path.join(output_dir, file_name+".tif.aux.xml"))
                shutil.move(raster+".tfw",
                            os.path.join(output_dir, file_name+".tfw"))
                track_image.append(raster)
                print(f"Moving {raster}")
    return 0


if __name__ == "__main__":
    main()
