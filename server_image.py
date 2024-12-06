import asyncio
from datetime import datetime
from pathlib import Path
import plotly.express as px
import numpy
from shiny import ui, render, reactive, Session
from shinywidgets import render_plotly

from river_segmentation.image_handler import ImageHandler


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
            image_handler = load_image_handler()
            p.set(1)
            ymax, xmax = image_handler.image_shape
            ui.update_numeric("xmin", value=0)
            ui.update_numeric("xmax", value=xmax)
            ui.update_numeric("ymin", value=0)
            ui.update_numeric("ymax", value=ymax)
            p.set(2)

    @reactive.Calc
    @reactive.event(input.load_image)
    def load_image_handler():
        with ui.Progress(min=1, max=3) as p:
            p.set(
                message="Téléversement en cours", detail="Peut prendre jusqu'à 1 minute"
            )
            p.set(1)
            image_handler = ImageHandler(
                image_path=Path(input.image_folder(), input.image_name()),
                transect_path=input.transect_path(),
            )
            p.set(2)
        return image_handler

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

    # @output
    # @render_widget
    @render_plotly
    @reactive.event(input.apply_threshold_values)
    def show_raster():
        image_handler = load_image_handler()
        subset = image_handler.rgbnir
        ndvi = image_handler.ndvi
        nir = image_handler.nir
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
            fig = px.imshow(ndvi, zmin=-1, zmax=1)
        elif input.image_visualisation() == "NIR":
            fig = px.imshow(nir, color_continuous_scale="icefire", zmin=0, zmax=255)
        else:
            raise ValueError("Image Visualisation not in RGB, NDVI or NIR")
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
        yield "image_name,ndvi,nir\n"
        yield f"{input.image_name()[:-3]},{input.ndvi_threshold()},{input.nir_threshold()}\n"
