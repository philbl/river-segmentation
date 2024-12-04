from shiny import ui, App, Session

from ui import ui_image
from server_image import server_image


ui_info = ui.page_fluid(ui.output_text_verbatim("general_informations"))

app_ui = ui.page_fluid(ui.h1("Choix et Segmentation d'ortho images"), ui_image)


def server(input, output, session: Session):
    server_image(input, output, session)


# This is a shiny.App object. It must be named `app`.
app = App(app_ui, server)
