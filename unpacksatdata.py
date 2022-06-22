"""Unzip the zip file from the satellite."""
import geojson
import zipfile
from fastapi import HTTPException
from settings import PATH_BUFFER, PATH_FIELDS
from makeimages import make_images_tiff
from loguru import logger


async def make_data_field(field_name: str) -> str:
    """Starts the function of unpacking and creating raster images of the field and NDVI field."""
    name_unzip_file = await unzip_file(field_name)
    await make_images_tiff(name_unzip_file, field_name)
    message = 'The satellite images have been processed and uploaded to the server.'
    return message
 

async def get_path_to_title_file(field_name: str) -> str:
    """Specifies the name of the downloaded file."""
    with open(f'{PATH_FIELDS}{field_name}/sat_field_{field_name}.geojson') as f:
        string_geojson = geojson.load(f)
        title_file =string_geojson.get('features')[0].get('properties').get('title')
    path_to_title_file =f'{PATH_BUFFER}sat_field_{field_name}/{title_file}'
    return path_to_title_file


async def unzip_file(field_name: str) -> str:
    """Unpacks a zip file with image data. Returns the path to the unpacked file."""
    path_to_title_file = await get_path_to_title_file(field_name)
    name_zip_file =f'{path_to_title_file}.zip' 
    try:
        with zipfile.ZipFile(name_zip_file, 'r') as zip_file:
            zip_file.extractall(f'{PATH_BUFFER}sat_field_{field_name}/')
        name_unzip_file = f'{path_to_title_file}.SAFE'
        logger.info('File zip unpacked')
        return name_unzip_file
    except FileNotFoundError as ex:
        logger.info(f'{ex}.No such file or directory.')
        raise HTTPException(status_code=500, detail='No such file or directory.')

