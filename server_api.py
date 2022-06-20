#FastAPI Server
from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from loguru import logger
from getsatdata import get_data
from fastapi.responses import FileResponse
import os
from unpacksatdata import make_data_field
from settings import PATH_BUFFER, PATH_FIELDS
import json
import fnmatch


logger.add("logger/debug.log", format="{time} {level} {message}", level="DEBUG", rotation="5:00")

# FastAPI app creation
app = FastAPI()


@app.get("/")
async def root():
    return JSONResponse(content={"message":"Hello from Agroapi"}, status_code=200)


@app.post("/make-field")
async def create_upload_file(
    file: UploadFile = File(description="name"),
):
    """Creating a new field directory. The client sends the file geojson. The server receives the file, creates a field with the file name and puts the starting geojson file in that directory."""
    directory_name = str(file.filename).rsplit('.', maxsplit=1)[0]
    if directory_name in os.listdir(PATH_BUFFER):
        message = f'This name {directory_name} already exists. Give the field a different name.'
        return Response(content=message, media_type="application/json")
    os.mkdir(f'{PATH_FIELDS}{directory_name}')
    path = f"{PATH_FIELDS}{directory_name}/{file.filename}"
    with open(path, 'wb') as f:
        content = await file.read()
        f.write(content)
        f.close()
    message = f"The directory for the field is created, the directory and 'field_mame' is: {directory_name}"
    return Response(content=message, media_type="application/json")


@app.post("/download-sat-field-data")
async def load_data_field(field_name: str = Form(...), username: str = Form(...), password: str = Form(...)):
    """Loads data from the satellite to the server."""
    if field_name not in os.listdir(PATH_FIELDS):
        raise HTTPException(status_code=404, detail=f"'{field_name}' not found")
    logger.info(f'path:{field_name}')
    message = await get_data(field_name, username, password)
    return Response(content=message, media_type="application/json")


@app.post("/run-make-field-images")
async def response_field(field_name: str = Form(...)):
    """Runs the process of creating field and NDVI images."""
    if field_name not in os.listdir(PATH_FIELDS):
        raise HTTPException(status_code=404, detail=f"'{field_name}' not found")
    logger.info(f'path:{field_name}')
    message = await make_data_field(field_name)
    return Response(content=message, media_type="application/json")


@app.get("/fields-name-files")
async def get_fields_registry(field_name: str = ''):
    """Returns to the client the list of files in the field directory."""
    if field_name not in os.listdir(PATH_FIELDS):
        raise HTTPException(status_code=404, detail=f"'{field_name}' not found")
    path_dir = f'{PATH_FIELDS}{field_name}'
    file_list = []
    for name in os.listdir(path_dir):
        path = os.path.join(path_dir, name)
        if os.path.isfile(path):
            file_list.append(path)
    files_js = jsonable_encoder(file_list)
    return JSONResponse(content={f"{field_name}":files_js}, status_code=200)




@app.get("/fields-names")
async def get_fields_registry():
    """Returns a list of saved field directories to the client."""
    path_dir = PATH_FIELDS
    file_list = []
    file_list.clear
    for name in os.listdir(path_dir):
        if name != 'buffer':
            path = os.path.join(path_dir, name)
            file_list.append(path)
    files_js = jsonable_encoder(file_list)
    return JSONResponse(content={"fields":files_js}, status_code=200)


@app.get("/sat-image")
async def response_sat_image(field_name: str = ''):
    """Returns JPEG image of the satellite image to the client."""
    if field_name not in os.listdir(PATH_FIELDS):
        raise HTTPException(status_code=404, detail=f"'{field_name}' not found")
    path_list = os.listdir(f'{PATH_FIELDS}{field_name}/')
    for file_name in path_list:
        if fnmatch.fnmatch(file_name, 'S*.jpeg'):
            path_file = f'{PATH_FIELDS}{field_name}/{file_name}'
    return FileResponse(path_file)


@app.get("/field-image")
async def response_field_image(field_name: str = ''):
    """Returns PNG image of the field to the client."""
    if field_name not in os.listdir(PATH_FIELDS):
        raise HTTPException(status_code=404, detail=f"'{field_name}' not found")
    path_file = f'{PATH_FIELDS}{field_name}/{field_name}_RGB_10_TCI_field.png'
    return FileResponse(path_file)


@app.get("/ndvi-image")
async def response_ndvi_image(field_name: str = ''):
    """Returns PNG image of the NDVI field to the client."""
    if field_name not in os.listdir(PATH_FIELDS):
        raise HTTPException(status_code=404, detail=f"'{field_name}' not found")
    path_file = f'{PATH_FIELDS}{field_name}/{field_name}_NDVI_10_field.png'
    return FileResponse(path_file)


@app.get("/field-image_jpeg")
async def response_ndvi_image(field_name: str = ''):
    """Returns JPEG image of the field to the client."""
    if field_name not in os.listdir(PATH_FIELDS):
        raise HTTPException(status_code=404, detail=f"'{field_name}' not found")
    path_file = f'{PATH_FIELDS}{field_name}/{field_name}_RGB_10_TCI_masked.jpeg'
    return FileResponse(path_file)


@app.get("/field-geojson")
async def response_field_geojson(field_name: str = ''):
    """Returns the initial geojson file to the client."""
    if field_name not in os.listdir(PATH_FIELDS):
        raise HTTPException(status_code=404, detail=f"'{field_name}' not found")
    path_file = f'{PATH_FIELDS}{field_name}/{field_name}.geojson'
    return FileResponse(path_file)


@app.get("/sat-geojson")
async def response_sat_geojson(field_name: str = ''):
    """Returns the geojson satellite product file to the client."""
    if field_name not in os.listdir(PATH_FIELDS):
        raise HTTPException(status_code=404, detail=f"'{field_name}' not found")
    path_file = f'{PATH_FIELDS}{field_name}/sat_field_{field_name}.geojson'
    return FileResponse(path_file)


@app.get("/field-middle-ndvi")
async def response_ndvi(field_name: str = ''):
    "Returns the middle value of the NDVI field to the client."
    if field_name not in os.listdir(PATH_FIELDS):
        raise HTTPException(status_code=404, detail=f"'{field_name}' not found")
    path_file = f'{PATH_FIELDS}{field_name}/{field_name}_NDVI.json'
    return FileResponse(path_file)

