from fastapi import FastAPI
from starlette.responses import HTMLResponse

app = FastAPI()

@app.get("/")
async def root():
    with open('index.html') as file:
        html = file.read()
    return HTMLResponse(content=html, status_code=200)

@app.get("/build_graph/user_id={user_id}&email={email}")
async def build_graph(user_id,email):
    print(user_id,email)
    return {"item_id": user_id, 'email':email}
