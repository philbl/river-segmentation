import asyncio
from datetime import datetime
from pathlib import Path
import plotly.express as px
import rasterio
from rasterio.features import geometry_mask
import numpy
import geopandas
from shiny import ui, render, reactive, Session
from shinywidgets import render_widget
from skimage import img_as_float32

from utils import get_water_rgb_array_from_transect_df, find_bounding_box


def server_image(input, output, session: Session):
    @reactive.Effect
    @reactive.event(input.see_image_list)
    def update_turbidity_slider_idx():
        image_list = [
            path.name
            for path in Path(input.image_folder()).iterdir()
            if path.suffix == ".tif"
        ]
        ui.update_select("image_name", choices=image_list),

    @reactive.Effect
    @reactive.event(input.load_image)
    def update_subset_bouding_box():
        with ui.Progress(min=1, max=2) as p:
            p.set(
                message="Téléversement en cours", detail="Peut prendre jusqu'à 1 minute"
            )
            subset, ndvi, nir = load_raster()
            p.set(1)
            ymax, xmax = nir.shape
            ui.update_numeric("xmin", value=0)
            ui.update_numeric("xmax", value=xmax)
            ui.update_numeric("ymin", value=0)
            ui.update_numeric("ymax", value=ymax)
            p.set(2)

    @reactive.Calc
    @reactive.event(input.load_image)
    def load_raster():
        with ui.Progress(min=1, max=3) as p:
            p.set(
                message="Téléversement en cours", detail="Peut prendre jusqu'à 1 minute"
            )
            img = rasterio.open(Path(input.image_folder(), input.image_name()))
            img_array = img.read()
            transect_polygon_df = geopandas.read_file(input.transect_path())
            transect_polygon_df = transect_polygon_df[
                transect_polygon_df["Backwater"] == 0
            ]
            transect_polygon_df = transect_polygon_df[transect_polygon_df["Lac"] == 0]
            transect_polygon_df = transect_polygon_df[
                ~transect_polygon_df["Slope"].isna()
            ]
            transect_polygon_df = transect_polygon_df[transect_polygon_df["Slope"] > 0]
            transect_polygon_df = transect_polygon_df.sort_values(by="PK").reset_index(
                drop=True
            )
            p.set(1)
            all_transect_polygon = get_water_rgb_array_from_transect_df(
                img, transect_polygon_df
            )
            river_mask = geometry_mask(
                all_transect_polygon.geoms,
                out_shape=img_array.shape[1:],
                transform=img.transform,
                invert=True,
            )
            p.set(2)
            xmin, xmax, ymin, ymax = find_bounding_box(
                numpy.atleast_3d(river_mask).transpose(2, 0, 1)
            )
            rgbnir_array = img_array.transpose(1, 2, 0)
            subset = rgbnir_array[ymin:ymax, xmin:xmax]
            subset_float = img_as_float32(subset)
            ndvi = (subset_float[:, :, 3] - subset_float[:, :, 0]) / (
                subset_float[:, :, 3] + subset_float[:, :, 0]
            )
            nir = subset[:, :, 3]
            p.set(3)
        return subset, ndvi, nir

    @reactive.Calc
    @reactive.event(input.apply_threshold_values)
    def get_threshold_value():
        ndvi_threshold = input.ndvi_threshold()
        nir_threshold = input.nir_threshold()
        use_nir = input.use_nir()
        use_ndvi = input.use_ndvi()
        xmin = input.xmin()
        xmax = input.xmax()
        ymin = input.ymin()
        ymax = input.ymax()
        return ndvi_threshold, nir_threshold, use_ndvi, use_nir, xmin, xmax, ymin, ymax

    @output
    @render_widget
    def show_raster():
        subset, ndvi, nir = load_raster()
        (
            ndvi_threshold,
            nir_threshold,
            use_ndvi,
            use_nir,
            xmin,
            xmax,
            ymin,
            ymax,
        ) = get_threshold_value()
        subset = subset[ymin:ymax, xmin:xmax]
        ndvi = ndvi[ymin:ymax, xmin:xmax]
        nir = nir[ymin:ymax, xmin:xmax]
        use_mask = use_ndvi or use_nir
        if use_mask:
            ndvi_mask = ndvi < ndvi_threshold if use_ndvi else numpy.ones_like(ndvi)
            nir_mask = nir < nir_threshold if use_nir else numpy.ones_like(nir)
            water_mask = ndvi_mask * nir_mask
        else:
            water_mask = numpy.zeros_like(ndvi)
        water_mask = water_mask.astype(bool)
        subset_plot = subset.copy()
        subset_plot[water_mask, 0] = 0
        if input.image_visualisation() == "RGB":
            fig = px.imshow(subset_plot[:, :, :3])
        elif input.image_visualisation() == "NDVI":
            fig = px.imshow(ndvi)
        elif input.image_visualisation() == "NIR":
            fig = px.imshow(nir, color_continuous_scale="icefire")
        fig.update_layout(
            autosize=False,
            width=1000,
            height=750,
            margin=dict(l=0, r=0, b=0, t=0, pad=0),
        )
        return fig

    @render.download(
        filename=lambda: f"{input.image_name()}_seuil_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
    )
    async def download_data():
        await asyncio.sleep(1)
        yield "ndvi,nir\n"
        yield f"{input.ndvi_threshold()},{input.nir_threshold()}\n"
