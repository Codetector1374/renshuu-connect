#!/bin/env python
import uvicorn

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse

from models import Action, EmptyRequest, AddNoteRequest, CanAddNotesRequest
from renshuu_api import RenshuuApi
from concurrent.futures import ProcessPoolExecutor
from collections import deque
import os
import sys

log = deque(maxlen=100)

def register_exception(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
        #print(await request.json())
        content = {"result": None, "error": exc_str}
        return JSONResponse(content=content, status_code=status.HTTP_200_OK)

class LogOutput(object):
    def write(self, string):
        log.append(string)
        pass

    def isatty(self):
        return False

sys.stdout = LogOutput()
sys.stderr = LogOutput()

app = FastAPI()

async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        exc_str = f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}"
        print(exc_str)
        content = {"result": None, "error": exc_str}
        return JSONResponse(content=content, status_code=status.HTTP_200_OK)

app.middleware('http')(catch_exceptions_middleware)

register_exception(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=PlainTextResponse)
async def root(showlog: str="0"):
    if showlog == "0":
        return ""
    msg = "Last 100 log messages:\n\n"
    msg += "".join(log)
    return msg

@app.get("/about", response_class=PlainTextResponse)
async def root(showlog: str = "0"):
    pid = os.getpid()
    return f"renshuu-connect is running!\nPID = {pid}"

@app.post("/")
async def root(request: EmptyRequest | AddNoteRequest | CanAddNotesRequest):
    api = RenshuuApi(request.key)

    if request.action is Action.deckNames:
        return api.schedules()
    elif request.action is Action.modelNames:
        return ["Default", "with jmdictId"]
    elif request.action is Action.modelFieldNames:
        return ["Japanese", "English", "jmdictId"]
    elif request.action is Action.canAddNotes:
        with ProcessPoolExecutor() as executor:
            resp = executor.map(api.canAddNote, request.params.notes)
        return list(resp)
    elif request.action is Action.addNote:
        return api.addNote(request.params.note)
    #elif request.action is Action.multi:
    #    return "TODO"
    elif request.action is Action.storeMediaFile:
        return ""
    elif request.action is Action.version:
        return 2

if __name__ == "__main__":
    if os.name == 'nt':
        import windows
        windows.setup_tray_icon()
    uvicorn.run(app, port=8765, log_level="warning")
