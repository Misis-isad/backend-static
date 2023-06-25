import sqlite3
import os

import uuid
from os import getcwd, remove
from fastapi import FastAPI, UploadFile, File, APIRouter, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
import dotenv

dotenv.load_dotenv()

app = FastAPI()

# get DOMAIN value from .env file
DOMAIN = os.getenv("DOMAIN")
FILEURL = f"{DOMAIN}/static/file/"


# create sqlite3 database with files table which contains id as str and filename as str


def init_db():
    print("initializing database")
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS files (id TEXT PRIMARY KEY, filename TEXT)"
    )
    conn.commit()
    conn.close()


def startup():
    # check if static folder exists if not create one
    if not os.path.exists("static"):
        os.mkdir("static")

    init_db()


# add record to database with id and filename
def add_record(filename: str) -> str:
    print("adding record to database")
    # generate unique id as md5 hash of filename and check if it exists in database
    new_id = uuid.uuid4().hex
    # get file extension frpom filename and add it to id
    new_id += "." + filename.split(".")[-1]
    # check if id exists in database
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE id=?", (new_id,))
    while cursor.fetchone():
        new_id = uuid.uuid4().hex
        new_id += "." + filename.split(".")[-1]
        cursor.execute("SELECT * FROM files WHERE id=?", (new_id,))

    cursor.execute("INSERT INTO files VALUES (?, ?)", (new_id, filename))
    conn.commit()
    conn.close()

    return new_id


def get_record(id: str):
    print("getting record from database")
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE id=?", (id,))
    record = cursor.fetchone()
    conn.close()
    return record


def get_all_records():
    print("getting all records from database")
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files")
    records = cursor.fetchall()
    # add file url to records
    records = [(FILEURL+i[0], i[1])for i in records]
    conn.close()
    return records


def delete_record(id: str):
    print("deleting record from database")
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM files WHERE id=?", (id,))
    conn.commit()
    conn.close()

    remove(getcwd() + "/static/" + id)


app.on_event("startup")(startup)

static_router = APIRouter(prefix="/static", tags=["static"])


@static_router.post("/upload")
async def upload_file(file: UploadFile = File(None)):
    print("uploading file")
    # add record to database
    if file.filename == None:
        raise HTTPException(status_code=400, detail="No file provided")
    new_id = add_record(file.filename)

    with open(f"static/{new_id}", "wb") as image:
        content = await file.read()
        image.write(content)
        image.close()
    return JSONResponse(content={"link": FILEURL+str(new_id)}, status_code=200)


@static_router.get("/download/{unique_id}")
def download_file(unique_id: str):
    # get record from database and send file with proper file type

    return FileResponse(
        path=getcwd() + "/static/" + unique_id,
        media_type="application/octet-stream",
        filename=unique_id,
    )


@static_router.get("/file/{unique_id}")
def get_file(unique_id: str):
    return FileResponse(path=getcwd() + "/static/" + unique_id)


@static_router.delete("/delete/file/{unique_id}")
def delete_file(unique_id: str):
    try:
        delete_record(unique_id)
        return JSONResponse(content={"removed": True}, status_code=200)
    except FileNotFoundError:
        return JSONResponse(
            content={"removed": False, "error_message": "File not found"},
            status_code=404,
        )


@static_router.get("/all")
async def get_all():
    records = get_all_records()
    return JSONResponse(content={"records": records}, status_code=200)

app.include_router(static_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
