import sqlite3
import os
from pydantic import BaseModel
from hashlib import md5
from os import getcwd, remove
from fastapi import FastAPI, UploadFile, File, APIRouter
from fastapi.responses import JSONResponse, FileResponse

app = FastAPI()

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
    new_id = md5(filename.encode("utf-8")).hexdigest()
    # check if id exists in database
    conn = sqlite3.connect("files.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE id=?", (new_id,))
    while cursor.fetchone():
        new_id = md5(filename.encode("utf-8")).hexdigest()
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
    conn.close()
    return records


app.on_event("startup")(startup)

static_router = APIRouter(prefix="/static", tags=["static"])


@static_router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    print("uploading file")
    # add record to database
    new_id = add_record(file.filename)

    with open(f"static/{new_id}", "wb") as image:
        content = await file.read()
        image.write(content)
        image.close()
    return JSONResponse(content={"filename": file.filename}, status_code=200)


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
        remove(getcwd() + "/static/" + unique_id)
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
