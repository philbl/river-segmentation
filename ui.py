from shiny import ui
from shinywidgets import output_widget


ui_image = ui.page_fluid(
    ui.h1("Exploration de filtre de pixel"),
    ui.row(
        ui.column(
            2,
            ui.input_text(
                "image_folder", "Dossier d'images", ""
            ),
        ),
        ui.column(
            2,
            ui.input_text(
                "transect_path",
                "Transect shapefile",
                "",
            ),
        ),
        ui.column(
            2, ui.input_action_button("see_image_list", "Voir Images existantes")
        ),
        ui.column(2, ui.input_select("image_name", "Sélectionner l'image", choices=[])),
        ui.column(2, ui.input_action_button("load_image", "Téléverser l'image")),
    ),
    ui.row(
        ui.column(
            1,
            ui.input_numeric(
                "ndvi_threshold",
                "Seuil NDVI",
                min=-1,
                max=1,
                step=0.01,
                value=0.55,
            ),
        ),
        ui.column(
            1,
            ui.input_numeric(
                "nir_threshold",
                "Seuil NIR",
                min=0,
                max=255,
                step=1,
                value=70,
            ),
        ),
        ui.column(
            1,
            ui.input_checkbox("use_ndvi", "Utiliser NDVI"),
        ),
        ui.column(
            1,
            ui.input_checkbox("use_nir", "Utiliser NIR"),
        ),
        ui.column(
            1,
            ui.input_numeric("xmin", "xmin", step=1, value=0),
        ),
        ui.column(
            1,
            ui.input_numeric("xmax", "xmax", step=1, value=0),
        ),
        ui.column(
            1,
            ui.input_numeric("ymin", "ymin", step=1, value=0),
        ),
        ui.column(
            1,
            ui.input_numeric("ymax", "ymax", step=1, value=0),
        ),
        ui.column(
            1,
            ui.input_action_button("apply_threshold_values", "Appliquer"),
        ),
        ui.column(
            1,
            ui.download_button("download_data", "Sauvegarder"),
        ),
    ),
    output_widget("show_raster"),
)
