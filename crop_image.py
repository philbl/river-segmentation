import geopandas
from shapely import overlaps
from pathlib import Path
from tqdm import tqdm

from river_segmentation.crop_image.utils import crop_image_under_from_2_images
from river_segmentation.crop_image.river_name_mapping import (
    get_river_save_name_from_index,
)


RIVER_NAME = ""  # Choices are DMT ESC MAN
INDEX_FILE_PATH = "D:/SERIF/ESC/PHOTOS/Index/Index_Ortho_utilises_ESC.shp"
IMAGE_FOLDER_PATH = "D:/SERIF/ESC/photos_crop_2024/"
DELETE_UNUSED_IMAGE_IN_FOLDER = False


if __name__ == "__main__":
    assert RIVER_NAME in ["DMT", "ESC", "MAN"]
    image_to_process_df = geopandas.read_file(INDEX_FILE_PATH)
    image_to_process_df = image_to_process_df.sort_values("Hierarchie").reset_index(
        drop=True
    )
    get_river_save_name_from_index_river = get_river_save_name_from_index(RIVER_NAME)
    image_to_process_df["nom_image_save"] = image_to_process_df["NOM_IMAGE"].apply(
        get_river_save_name_from_index_river
    )
    if DELETE_UNUSED_IMAGE_IN_FOLDER:
        for image_path in filter(
            lambda path: ".tif" in str(path), Path(IMAGE_FOLDER_PATH).iterdir()
        ):
            if (
                image_path.name.split(".")[0]
                not in image_to_process_df["nom_image_save"].values
            ):
                image_path.unlink()

    for image_under_index, image_under_row in tqdm(
        image_to_process_df[:-1].iterrows(), total=len(image_to_process_df[:-1])
    ):
        for image_over_index, image_over_row in image_to_process_df[
            image_under_index + 1 :
        ].iterrows():
            image_under_name = image_under_row["nom_image_save"]
            image_over_name = image_over_row["nom_image_save"]
            if overlaps(image_under_row.geometry, image_over_row.geometry):
                crop_image_under_from_2_images(
                    Path(IMAGE_FOLDER_PATH, image_under_name),
                    Path(IMAGE_FOLDER_PATH, image_over_name),
                )
