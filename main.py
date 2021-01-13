import io
import json
import os
import random
import smtplib
import time
import networkx as nx
import matplotlib.pyplot as plt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from fastapi import FastAPI, Query, Path, BackgroundTasks
from starlette.responses import HTMLResponse, Response, StreamingResponse
from email_validator import validate_email, EmailNotValidError
from settings import *

app = FastAPI()

def send_email(from_email, to_email, password, message):
    msg = MIMEMultipart()
    msg['Subject'] = 'Graph friends result'
    msg.attach(MIMEText(message, 'html'))
    server = smtplib.SMTP('smtp.gmail.com: 587')
    server.starttls()
    server.login(from_email, password)
    server.sendmail(from_email, to_email, msg.as_string())
    server.quit()

def parse_friends(user_id):
    s = requests.Session()
    s.proxies = {
        'https': '139.162.11.25:8888',
        'http': '80.241.222.138:0080',
    }
    res = s.get(f"{BASE_URL}/friends.get?user_id={user_id}&fields=name&access_token={ACCESS_TOKEN}&v={API_VERSION}")
    return res.json()

def process_request(user_id, accuracy: float=1, email: str=None):
    filename = get_random_filename()
    graph = build_graph(user_id, accuracy)
    draw_graph(graph, filename)
    full_path = f'images/{filename}.png'

    with open(full_path, 'rb') as file:
        img_data = file.read()

    if os.path.exists(full_path):
        os.remove(full_path)

    if email is not None:
        send_email(ADMIN_EMAIL,email,ADMIN_PASSWORD,img_data)

    return img_data

def build_graph(user_id, accuracy: float = 1):
    mg = nx.DiGraph()
    mg.add_node('Main user')
    main_friends = parse_friends(user_id)['response']['items']
    friends_of_friend = {}
    for friend in main_friends:
        mg.add_node(friend['first_name'] + friend['last_name'])
        mg.add_edge(friend['first_name'] + friend['last_name'], 'Main user')
        try:
            friends_of_friend = parse_friends(friend['id'])['response']['items']
            print(friends_of_friend)
            friends_of_friend[friend['first_name'] + friend['last_name']] = friends_of_friend[:int(len(friends_of_friend)*accuracy)]
        except Exception as e:
            print(e)

    for user in friends_of_friend:
        for friend in friends_of_friend[user]:
            mg.add_node(friend['first_name'] + friend['last_name'])
            mg.add_edge(friend['first_name'] + friend['last_name'], user)

    return mg

def get_random_filename():
    return str(round(time.time() * (10 ** 6))) + str(random.randint(0, 10 ** 7))

def draw_graph(g, filename):
    plt.figure(figsize=(30,30))
    nx.draw_random(g, node_size=50, font_size=3, with_labels=True, font_weight='bold')
    plt.savefig(f'images/{filename}.png',dpi=250)
    plt.clf()

@app.get("/")
async def root():
    with open('index.html') as file:
        html = file.read()
    return HTMLResponse(content=html, status_code=200)

@app.get("/graph/user_id={user_id}")
async def graph(background_tasks: BackgroundTasks,
                      user_id: int = Path(None, title="ID of the Vk user", gt=0),
                      accuracy: float = Query(1.0, ge=0.0, le=1.0),
                      email: str = Query(None, max_length=50)):
    try:
        if email:
            validate_email(email)
            background_tasks.add_task(process_request, user_id, accuracy, email)
            return Response(json.dumps({'Answer':'Your request accepted, we will send result to your email'}))
        else:
            result_img = process_request(user_id,accuracy)
            return StreamingResponse(result_img, media_type="image/png")
    except EmailNotValidError as e:
        return Response(str(e),status_code=400)
    except Exception as e:
        return Response(str(e), status_code=500)
