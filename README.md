# AgroApi
## Agroapi server

The server processes satellite data from request.

### Commands

* /make-field - form-data: geojson file - a file with the coordinates of the field of interest. Create new field.
* /download-sat-field-data - form-data: field_name, username, password. Load sattelite information for the specified field.
* /run-make-field-images - form-data: field_name. NDVI calculation, field and ndvi images creation.
* /fields-name-files - params: field_name. Return list of fild files after making.
* /fields-names - Return list of created fields
* /sat-image - params: field_name. Return general satellite image.
* /field-image - params: field_name. Return image of the field format png.
* /ndvi-image - params: field_name. Return NDVI image of the field format png.
* /field-image_jpeg - params: field_name. Return image of the field format jpeg.
* /field-geojson - params: field_name. Source field file geojson (field coordinates).
* /sat-geojson - params: field_name. Information from the satellite over the entire territory in the geojson format.
* /field-middle-ndvi - params: field_name. Middle field NDVI.
* /delete_field - params: field_name. Deleting field information.


### Process

User logs in to **https://scihub.copernicus.eu**. The site provides information from satellites.<br>
User creates a geojson file with the coordinates of the agricultural field. It is possible to use the site **https://geojson.io**<br>
For the request you need: geojson file, Username account, Password account.<br>
scihub.copernicus sends a response with information about its coverage area of about 200km x 200km with zip file (about 1Gb) raster bands.<br>
The AgroApi server receives the territory information in geojson format. For the period from the request. The filter is set to summer time with the lowest cloud coverage.<br>
The AgroApi server unpacks the zip file. Creates RGB raster field. Crops the selected field. Calculates NDVI (Normalized Difference Vegetation Index) from Red and Nir bands. Creates raster and crops the selected field. Obtains middle NDVI from the generated sequence for the selected field. Displays in PNG format pictures.<br>
Raster data processing can take up to 5 minutes!<br>
After creating images and calculating NDVI, the server deletes the downloaded zip file (more than 1Gb) and the resulting intermediate raster images (about 0.3Gb).


### Composition

* server_api.py - entry point
* getsatdata.py - receiving satellite data
* unpacksatdata.py - unpacking satellite data
* makeimages.py - making agro filed images, calculation ndvi satellite raster
* converting.py - images converting TIFF to PNG and JPEG, calculation ndvi field
* /fields - directory for the fields created
* /fields/buffer - directory for temporary large zip files from the satellite
* /logger - directory for log files

### DevelopmentrRequirements

#### Python 3.10.2
* FastAPI
* rasterio
* sentinelsat
* numpy
* pillow
* geopandas
* geojson
* matplotlib
* loguru


### Run server
#### On localhost:
* run server http://127.0.0.1:8000: uvicorn server_api:app --reload