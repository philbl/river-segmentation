import os
from river_segmentation.crop_image.index_processer import IndexProcesser

def main():
    path_project = r"path/to/your/river/photos"
    # Create instance of the index processer
    processer = IndexProcesser()
    # The index file must be in a subfolder within the TIF file's folder 
    # The structure must be as follows: PHOTOS_TIF/Index/index_file_name.shp
    # IMPORTANT: The Index folder must start with capital I
    processer.index = os.path.join(path_project,"Index/index_file_name.shp")
    processer.photos = path_project
    processer.reproject_index("2947") #Select the EPSG code based on the TIF image projection
    processer.trim_index()
    #This is the prefix just before the extention. For example if your file's name is
    # q16039_453_30cm_f05.tif the prefix is "30cm_f05".
    processer.create_box_from_extent("file_prefix")
    # This will save the clipped index and this index can be used to subsequently clip the photos
    processer.clip_overlapping_features()
    return 0


if __name__ == "__main__":
    main()
