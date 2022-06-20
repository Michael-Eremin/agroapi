"""Receiving data from the satellite."""
from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from loguru import logger
import geojson
from settings import USER, PASSWORD, PATH_API, PATH_FIELDS, PATH_BUFFER



async def _download_sat_jpeg(api: SentinelAPI, id_product: str, field_name: str) -> None:
    api.download_quicklook(id_product, f'{PATH_FIELDS}{field_name}/')


async def _download_data_from_sat(api: SentinelAPI, field_name: str, products_from_sat: dict[str, dict]) -> None:
    api.download_all(products_from_sat, directory_path=f'{PATH_BUFFER}sat_field_{field_name}')


async def _get_id_product(product_geojson: geojson) -> str:
        try:
            id_product = product_geojson.get('features')[0].get('properties').get('uuid')
        except IndexError:
            print("The field is not received. Expand the range of the query: date, cloudcoverpercentage.")
        return id_product


async def _get_product_geojson(api: SentinelAPI, products_from_sat: dict[str, dict], field_name: str) -> geojson:
    product_geojson = api.to_geojson(products_from_sat)
    with open(f'{PATH_FIELDS}{field_name}/sat_field_{field_name}.geojson', 'w') as f:
        geojson.dump(product_geojson, f)
    return product_geojson


async def _get_products_from_sat(api: SentinelAPI, path_file_geojson: str) -> dict[str, dict]:
    footprint = geojson_to_wkt(read_geojson(path_file_geojson))
    products_from_sat = api.query(footprint,
                         date=('20220415','20220615'), platformname='Sentinel-2',
                         order_by='cloudcoverpercentage',
                         processinglevel='Level-2A',
                         cloudcoverpercentage=(0, 10),
                         limit=1)
    return products_from_sat


def _get_api() -> SentinelAPI:
    api = SentinelAPI(USER, PASSWORD, PATH_API)
    logger.info('API connected')
    return api


async def get_data(field_name: str) -> str:
    """Connects to SentinelAPI and receives data from the satellite."""
    path_file_geojson=f'{PATH_FIELDS}{field_name}/{field_name}.geojson'
    api = _get_api()
    products_from_sat = await _get_products_from_sat(api, path_file_geojson)

    product_geojson = await _get_product_geojson(api, products_from_sat, field_name)
    logger.info(f'product_geojson:{product_geojson}')
        
    id_product = await _get_id_product(product_geojson)
    logger.info(f'id_product:{id_product}')
    
    await _download_data_from_sat(api, field_name, products_from_sat)
    await _download_sat_jpeg(api, id_product, field_name)
    logger.info('The data from the satellite is downloaded')
    return "The data from the satellite is downloaded."
    

       