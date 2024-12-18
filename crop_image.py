import geopandas
from shapely import overlaps
from pathlib import Path
import rasterio
from tqdm import tqdm

from river_segmentation.crop_image.utils import crop_image_under_from_2_images
from river_segmentation.crop_image.river_name_mapping import (
    get_river_save_name_from_index,
)


RIVER_NAME = "MAP"
INDEX_FILE_PATH = (
    "D:/SERIF/MAP/PHOTOS/Index_mathias_2024/Index_ortho_utilisees_assemetquagan.shp"
)
IMAGE_FOLDER_PATH = "D:/SERIF/MAP/phots_crop_atg/"
DELETE_UNUSED_IMAGE_IN_FOLDER = False


if __name__ == "__main__":
    assert RIVER_NAME in ["DMT", "ESC", "MAN", "YRK", "STJ", "TRI", "MAP", "SMRNE"]
    image_to_process_df = geopandas.read_file(INDEX_FILE_PATH)
    hierarchie_col_name = (
        "Hierarchie" if "Hierarchie" in image_to_process_df.columns else "HIERARCHIE"
    )
    image_to_process_df = image_to_process_df.sort_values(
        hierarchie_col_name
    ).reset_index(drop=True)
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
        image_under_name = image_under_row["nom_image_save"]
        if Path(IMAGE_FOLDER_PATH, image_under_name).exists() is False:
            continue
        for image_over_index, image_over_row in image_to_process_df[
            image_under_index + 1 :
        ].iterrows():
            image_over_name = image_over_row["nom_image_save"]
            if Path(IMAGE_FOLDER_PATH, image_over_name).exists() is False:
                continue
            if overlaps(image_under_row.geometry, image_over_row.geometry):
                crop_image_under_from_2_images(
                    Path(IMAGE_FOLDER_PATH, image_under_name),
                    Path(IMAGE_FOLDER_PATH, image_over_name),
                )

    for image_name_save in image_to_process_df["nom_image_save"]:
        with rasterio.open(Path(IMAGE_FOLDER_PATH, image_name_save), "r+") as dataset:
            dataset.nodata = 0