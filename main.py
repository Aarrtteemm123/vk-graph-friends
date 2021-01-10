from fastapi import FastAPI, Query, Path
from starlette.responses import HTMLResponse
from email_validator import validate_email, EmailNotValidError

app = FastAPI()

@app.get("/")
async def root():
    with open('index.html') as file:
        html = file.read()
    return HTMLResponse(content=html, status_code=200)

@app.get("/build_graph/user_id={user_id}")
async def build_graph(user_id: int = Path(None, title="The ID of the item to get", gt=0), email: str = Query(None, max_length=50)):

    return {"item_id": user_id, 'email':email}
