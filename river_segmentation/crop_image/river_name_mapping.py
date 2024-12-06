def get_river_save_name_from_index(river_name):
    if river_name == "ESC":
        return get_river_save_name_from_index_esc
    if river_name == "MAN":
        return get_river_save_name_from_index_man
    if river_name == "DMT":
        return get_river_save_name_from_index_dmt


def get_river_save_name_from_index_dmt(nom_image):
    save_name = f"{nom_image.replace('_rgb', '')}_4bandes_ortho.tif"
    return save_name


def get_river_save_name_from_index_man(nom_image):
    save_name = f"{nom_image}_4bandes_ortho.tif"
    return save_name


def get_river_save_name_from_index_esc(nom_image):
    save_name = nom_image
    return save_name
