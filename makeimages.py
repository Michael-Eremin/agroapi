"""Creation of field and NDVI field image files."""
from fastapi import HTTPException
import geopandas as gpd
from rasterio.mask import mask
from settings import PATH_FIELDS, PATH_BUFFER
import glob
import rasterio as rio
from converting import convert_ndvi_tiff_to_jpeg, convert_rgb_tiff_to_jpeg, make_field_image, make_ndvi_image
from loguru import logger
import shutil
import os


URL = str


async def delete_data_field(field_name: str) -> None:
    """Deletes all information about the field."""
    path_to_field_name = f'{PATH_FIELDS}{field_name}'
    try:
        shutil.rmtree(path_to_field_name)
        logger.info(f'Field "{field_name}" removed')
    except OSError as e:
        logger.info(f'Error "Field "{field_name}" : {e.strerror}')


def make_response_to_client(final_field: str, final_NDVI: str) ->str:
    """Makes a message to the client about the end of the image creation process."""
    message = f'{final_field}, {final_NDVI}.'
    return message


def delete_base_files(field_name: str) ->None:
    """Deletes used source files of large size."""
    path_to_buffer = f'{PATH_BUFFER}sat_field_{field_name}'
    path_to_field_name = f'{PATH_FIELDS}{field_name}/{field_name}'
    try:
        shutil.rmtree(path_to_buffer)
        logger.info(f'Buffer "sat_field_{field_name}" removed')
    except OSError as e:
        logger.info(f'Error "sat_field_{field_name}" : {e.strerror}')

    delete_list = [
        f'{path_to_field_name}_NDVI_10.tiff',
        f'{path_to_field_name}_NDVI_10_masked.tiff',
        f'{path_to_field_name}_RGB_10_TCI.tiff',
        f'{path_to_field_name}_RGB_10_TCI_masked.tiff'
        ]
    for file_path in delete_list:
        try:
            os.remove(file_path)
            logger.info(f'Files from {delete_list}" removed')
        except OSError as e:
            logger.info(f'Error: {file_path} : {e.strerror}')



async def make_images_tiff(name_unzip_file: URL, field_name: str) ->str:
    """Runs the image creation and deletion functions of the source files."""
    final_field = await make_field_masked_image_tiff(name_unzip_file, field_name)
    final_NDVI = await make_field_ndvi_image_tiff(name_unzip_file, field_name)
    message = make_response_to_client(final_field, final_NDVI)
    delete_base_files(field_name)
    return message


async def get_path_to_band_file(name_unzip_file: URL, band: str) ->URL:
    """Makes path to band"""
    path = f'{name_unzip_file}/GRANULE/*/IMG_DATA/R10m/*{band}'
    path_to_band = glob.glob(path)[0]
    return path_to_band


def get_field_data_from_geojson(field_name: str) -> gpd.geodataframe.GeoDataFrame:
    df = gpd.read_file(f'{PATH_FIELDS}/{field_name}/{field_name}.geojson')
    field_data = df.to_crs({'init': 'epsg:32637'})
    print(type(field_data))
    return field_data


async def make_field_masked_image_tiff(name_unzip_file: URL, field_name: str) -> str:
    """Creates a raster image of the field."""
    try:
        logger.info('make_field_masked_image_tiff')
        path_to_field_folder = f'{PATH_FIELDS}{field_name}/'
        TCI = rio.open(await get_path_to_band_file(name_unzip_file, 'TCI_10m.jp2'), driver='JP2OpenJPEG')
        field_data = get_field_data_from_geojson(field_name)
        rgb_profile = TCI.profile
        rgb_profile.update(
                    driver="GTiff",
                    count=3,
                    photometric="RGB",
                    compress="LZW",
                    bigtiff="IF_NEEDED",
                    tiled=True,
                    blockxsize=256,
                    blockysize=256,
                    crs = 32637
                    )

        with rio.open(f'{path_to_field_folder}{field_name}_RGB_10_TCI.tiff','w', **rgb_profile) as rgb:
            rgb.write(TCI.read())
            rgb.close()
        
        with rio.open(f'{path_to_field_folder}{field_name}_RGB_10_TCI.tiff') as src:
            out_image, out_transform = mask(src, field_data.geometry, crop=True)
            out_meta = src.meta.copy()
            out_meta.update({"driver": "GTiff",
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform})
            logger.info(f'make_field_masked_image_tiff-out_meta: {out_meta}')
        
        with rio.open(f'{path_to_field_folder}{field_name}_RGB_10_TCI_masked.tiff', "w", **out_meta) as dest:
            dest.write(out_image)

        make_field_image(path_to_field_folder, field_name)

        path_to_rgb_masked_tiff = f'{path_to_field_folder}{field_name}_RGB_10_TCI_masked.tiff'
        convert_rgb_tiff_to_jpeg(path_to_field_folder, field_name, path_to_rgb_masked_tiff)
        return 'Field image created'
    except ValueError as ex:
        logger.info(f'{ex}')
        raise HTTPException(status_code=500, detail=f'The field {field_name} is not covered by the received raster from the satellite. Change the request coordinates.')
    
        


async def make_field_ndvi_image_tiff(name_unzip_file: str, field_name: str) -> str:
    """Calculates NDVI and cretes an NDVI image."""
    logger.info('make_field_ndvi_image_tiff')
    path_to_field_folder = f'{PATH_FIELDS}{field_name}/'
    name_unzip_file = name_unzip_file
    
    b8 = rio.open(await get_path_to_band_file(name_unzip_file, 'B08_10m.jp2'), driver='JP2OpenJPEG')
    b4 = rio.open(await get_path_to_band_file(name_unzip_file, 'B04_10m.jp2'), driver='JP2OpenJPEG')
    red = b4.read()
    nir = b8.read()
    ndvi = (nir.astype(float) - red.astype(float)) / (nir+red)
    meta = b4.meta
    meta.update(driver='GTiff')
    meta.update(dtype=rio.float32)

    with rio.open(f'{path_to_field_folder}{field_name}_NDVI_10.tiff', 'w', **meta) as f:
        f.write(ndvi.astype(rio.float32))
    field_data = get_field_data_from_geojson(field_name)
    with rio.open(f'{path_to_field_folder}{field_name}_NDVI_10.tiff') as f:
        out_image, out_transform = mask(f, field_data.geometry, crop=True)
        out_meta = f.meta.copy()
        out_meta.update({"driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform})
        logger.info(f'make_field_ndvi_image_tiff-out_meta: {out_meta}')
    with rio.open(f'{path_to_field_folder}{field_name}_NDVI_10_masked.tiff', "w", **out_meta) as f:
        f.write(out_image)
    
    path_to_ndvi_masked_tiff = f'{path_to_field_folder}{field_name}_NDVI_10_masked.tiff'
    middle_ndvi = convert_ndvi_tiff_to_jpeg(path_to_field_folder, field_name, path_to_ndvi_masked_tiff)

    make_ndvi_image(path_to_field_folder, field_name, middle_ndvi)

    return 'NDVI calculated'
