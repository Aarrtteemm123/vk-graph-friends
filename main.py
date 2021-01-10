from fastapi import FastAPI, Query, Path
from starlette.responses import HTMLResponse, Response
from email_validator import validate_email, EmailNotValidError
import json

app = FastAPI()

@app.get("/")
async def root():
    with open('index.html') as file:
        html = file.read()
    return HTMLResponse(content=html, status_code=200)

@app.get("/build_graph/user_id={user_id}")
async def build_graph(user_id: int = Path(None, title="The ID of the item to get", gt=0), email: str = Query(None, max_length=50)):
    try:
        if email:
            validate_email(email)
    except EmailNotValidError as e:
        return Response(str(e),status_code=400)
    except Exception as e:
        return Response(str(e), status_code=500)
    data = {'user_id': user_id, 'email':email}
    return Response(json.dumps(data, default=lambda x: x.__dict__))
