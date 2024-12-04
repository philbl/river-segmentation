import geopandas
from shapely import overlaps
from pathlib import Path
from tqdm import tqdm

from crop_image.utils import crop_image_under_from_2_images


INDEX_FILE_PATH = "D:/SERIF/MAN/PHOTOS/Index/Index_ortho_utilisees.shp"
IMAGE_FOLDER_PATH = "D:/SERIF/DMT/photos_crop/"

if __name__ == "__main__":
    image_to_process_df = geopandas.read_file(INDEX_FILE_PATH)
    image_to_process_df = image_to_process_df.sort_values("Hierarchie").reset_index(
        drop=True
    )
    image_to_process_df["nom_image_save"] = image_to_process_df["NOM_IMAGE"].apply(
        lambda nom_image: f"{nom_image}_4bandes_ortho"
    )
    for image_path in filter(
        lambda path: ".tif" in str(path), Path(IMAGE_FOLDER_PATH).iterdir()
    ):
        if (
            image_path.name.split(".")[0]
            not in image_to_process_df["nom_image_save"].values
        ):
            print(image_path)
            image_path.unlink()

    for image_under_index, image_under_row in tqdm(
        image_to_process_df[:-1].iterrows(), total=len(image_to_process_df[:-1])
    ):
        for image_over_index, image_over_row in image_to_process_df[
            image_under_index + 1 :
        ].iterrows():
            image_under_name = f"{image_under_row['nom_image_save']}.tif"
            image_over_name = f"{image_over_row['nom_image_save']}.tif"
            if overlaps(image_under_row.geometry, image_over_row.geometry):
                crop_image_under_from_2_images(
                    Path(IMAGE_FOLDER_PATH, image_under_name),
                    Path(IMAGE_FOLDER_PATH, image_over_name),
                )
