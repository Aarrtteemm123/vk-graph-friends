import io
import json
import time

import requests
from fastapi import FastAPI, Query, Path, BackgroundTasks
from starlette.responses import HTMLResponse, Response, StreamingResponse
from email_validator import validate_email, EmailNotValidError
from settings import *

app = FastAPI()

def parse_data(user_id):
    s = requests.Session()
    s.proxies = {
        'http': '192.109.165.139:0080',
        'https': '85.14.243.31:3128',
    }
    res = s.get(f"{BASE_URL}/friends.get?user_id={user_id}&fields=name&access_token={ACCESS_TOKEN}&v={API_VERSION}")
    return res.json()

def build_graph(user_id, email: str=None):
    parse_data(user_id)
    if email is not None:
        pass
    else:
        pass
    return 'ok'

@app.get("/")
async def root():
    with open('index.html') as file:
        html = file.read()
    return HTMLResponse(content=html, status_code=200)

@app.get("/graph/user_id={user_id}")
async def graph(background_tasks: BackgroundTasks,
                      user_id: int = Path(None, title="ID of the Vk user", gt=0),
                      email: str = Query(None, max_length=50)):
    try:
        if email:
            validate_email(email)
            background_tasks.add_task(build_graph, user_id, email)
            return Response(json.dumps({'Answer':'Your request accepted, we will send result to your email'}))
        else:
            result_img = build_graph(user_id)
            return StreamingResponse(io.BytesIO(result_img.tobytes()), media_type="image/png")
    except EmailNotValidError as e:
        return Response(str(e),status_code=400)
    except Exception as e:
        return Response(str(e), status_code=500)
