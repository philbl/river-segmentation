import os
from river_segmentation.crop_image.index_processer import IndexProcesser

PATH_PROJECT = r"D:\SERIF\BNV\PHOTOS"

# The index file must be in a subfolder within the TIF file's folder
# The structure must be as follows: PHOTOS_TIF/Index/index_file_name.shp
# IMPORTANT: The Index folder must start with capital I
INDEX_SHP_PATH = os.path.join(PATH_PROJECT, "Index/index_BNV_tributaires.shp")

# Add the river center line shp file for the basin.
RIVER_CENTER_LINE = r"D:\SERIF\BNV\Ligne_BNV_principale_tributaires.shp"

CRS = "2947"  # Select the EPSG code based on the TIF image projection

# This is the prefix just before the extention. For example if your file's name is
# q16039_453_30cm_f05.tif the prefix is "30cm_f05".
FILE_PREFIX = "30cm_f05"


def main():
    # Create instance of the index processer
    processer = IndexProcesser()
    #Set the base files to process
    processer.photos = PATH_PROJECT
    processer.index = INDEX_SHP_PATH
    processer.center_line = RIVER_CENTER_LINE
    # Start processing
    processer.reproject_shp(CRS)
    processer.trim_index()
    processer.create_box_from_extent(FILE_PREFIX)
    processer.find_intersections()
    # This will save the clipped index and this index can be used to subsequently clip the photos
    # processer.clip_overlapping_features()
    # return 0


if __name__ == "__main__":
    main()
