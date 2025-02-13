#!/bin/python3
from fastapi import FastAPI, Request, Response, Header
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import os

# Set up FastAPI app
app = FastAPI()
PORT = 80
# Define template engine
templates = Jinja2Templates(directory="templates")

# Define video directory
dirname = "./"
videodir = os.path.join(dirname, "videos")
videos = [f for f in os.listdir(videodir) if f.endswith(('.mp4', '.avi', '.mkv'))]

# Video streaming function with range request handling
def generate_video_chunk(file_path, start: int = 0, end: int = None, chunk_size=1024*1024):
    file_size = os.path.getsize(file_path)

    if end is None or end >= file_size:
        end = file_size - 1

    with open(file_path, "rb") as video_file:
        video_file.seek(start)
        while start <= end:
            bytes_to_read = min(chunk_size, end - start + 1)
            yield video_file.read(bytes_to_read)
            start += bytes_to_read

@app.get("/stream-video/{video_filename}")
async def stream_video(video_filename: str, range: str = Header(None)):
    file_path = os.path.join(videodir, video_filename)

    if not os.path.exists(file_path):
        return Response("File not found", status_code=404)

    file_size = os.path.getsize(file_path)
    start, end = 0, file_size - 1

    if range:
        byte_range = range.replace("bytes=", "").split("-")
        start = int(byte_range[0]) if byte_range[0] else 0
        end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else file_size - 1

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Content-Length": str(end - start + 1),
        "Content-Type": "video/mp4",
    }

    return StreamingResponse(generate_video_chunk(file_path, start, end), status_code=206, headers=headers)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("main.html", {"request": request, "videos": videos})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=PORT, reload=True)
