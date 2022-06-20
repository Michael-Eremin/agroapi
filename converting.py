"""Convert raster images to JPEG and PNG formats, calculate NDVI."""
import numpy as np
from PIL import Image
import rasterio as rio
from matplotlib import pyplot as plt
from rasterio.plot import show
import json
from loguru import logger


URL = str

def make_ndvi_file(path_to_field_folder: URL, field_name: str, middle_ndvi: float) -> None:
    """Creates a json file and writes the NDVI data."""
    with open(f'{path_to_field_folder}{field_name}_NDVI.json', "w") as write_file:
        data = {
            "ndvi_data": {
                          "middle_ndvi": middle_ndvi,
                            }
                        }
        json.dump(data, write_file)
        logger.info(f'ndvi_file saved: {data}')


def convert_rgb_tiff_to_jpeg(path_to_field_folder: URL, field_name: str, path_to_rgb_masked_tiff: URL):
    """Converts the raster image of the field to JPEG format."""
    img = Image.open(path_to_rgb_masked_tiff)
    img = img.convert("RGB")
    img.save(f'{path_to_field_folder}{field_name}_RGB_10_TCI_masked.jpeg')
    logger.info('RGB_10_TCI_masked.jpeg saved')


def convert_ndvi_tiff_to_jpeg(path_to_field_folder: URL, field_name: str, path_to_ndvi_masked_tiff: URL) -> float:
    """Converts the raster NDVI image to JPEG format. Calculates the average NDVI of field."""
    path_to_ndvi_masked_jpeg = f'{path_to_field_folder}{field_name}_NDVI_10_masked.jpeg'
    image = Image.open(path_to_ndvi_masked_tiff)
    array_img = np.asarray(image)
    array_wuthout_null = array_img[array_img != 0]
    middle_array_img = round(float(np.nanmean(array_wuthout_null)), 2)
    min_array_img = np.nanmin(array_wuthout_null)
    max_array_img = np.nanmax(array_wuthout_null)
    array_img_new = np.uint8(np.interp(array_img, (min_array_img, max_array_img), (0, 255)))
    middle_array_img_new = np.nanmean(array_img_new)
    logger.info(f'middle_array_img_new: {middle_array_img_new}')
    logger.info(f'NDVI: min: {min_array_img}, max: {max_array_img}, middle: {middle_array_img}')
    im = Image.fromarray(array_img_new)
    im.save(path_to_ndvi_masked_jpeg)
    logger.info('NDVI_10_masked.jpeg saved')
    make_ndvi_file(path_to_field_folder, field_name, middle_array_img)   
    return middle_array_img


def make_field_image(path_to_field_folder: URL, field_name: str) -> None:
    """Makes field image PNG from raster image"""
    with rio.open(f'{path_to_field_folder}{field_name}_RGB_10_TCI_masked.tiff') as img:
        plt.figure(figsize=(1.6, 1.2))
        plt.ticklabel_format(style='plain')
        show(img.read(), transform=img.transform, title=f'Field: "{field_name}"') 
        plt.yticks(fontsize=3,)
        plt.xticks(fontsize=3,)
        plt.title(f'Field: "{field_name}"', fontdict ={'fontsize': 4}, pad=6)
        plt.savefig(f'{path_to_field_folder}{field_name}_RGB_10_TCI_field.png' , dpi=300, bbox_inches='tight')
        logger.info('RGB_10_TCI_field.png saved')


def make_ndvi_image(path_to_field_folder: URL, field_name: str, middle_ndvi: float):
    """Makes NDVI image PNG from raster image"""
    with rio.open(f'{path_to_field_folder}{field_name}_NDVI_10_masked.tiff') as img:

        plt.figure(figsize=(1.6, 1.2))
        plt.ticklabel_format(style='plain')
        im = plt.imshow(img.read(1), cmap='RdYlGn')
        show(img.read(1), transform=img.transform, cmap='RdYlGn') 
        # show(img.read(1), transform=img.transform, cmap='RdYlGn', title=f'Field: "{field_name}"') 
        plt.yticks(fontsize=3,)
        plt.xticks(fontsize=3,)
        plt.title(f'Field: "{field_name}", middle NDVI: {middle_ndvi}', fontdict ={'fontsize': 4}, pad=6)

        cb = plt.colorbar(im)
        for t in cb.ax.get_yticklabels():
            t.set_fontsize(3)

        cb.set_label('NDVI', fontsize=4)
        plt.savefig(f'{path_to_field_folder}{field_name}_NDVI_10_field.png' , dpi=300, bbox_inches='tight')
        logger.info('NDVI_10_field.png saved')

