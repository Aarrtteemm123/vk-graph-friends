import json, os, random, time, requests, base64
import networkx as nx
import matplotlib.pyplot as plt
from fastapi import FastAPI, Query, Path, BackgroundTasks
from sendgrid import SendGridAPIClient
from starlette.responses import HTMLResponse, Response
from email_validator import validate_email, EmailNotValidError
from settings import *
from sendgrid.helpers.mail import *

app = FastAPI()

for file in os.listdir('images'):
    os.remove(f'images/{file}')

def send_email(from_email, to_email, text, img):
    print('sending email...')

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject='Vk graph friends API result',
        html_content=f'<strong>{text}</strong>'
    )

    encoded_file = base64.b64encode(img).decode()

    attachedFile = Attachment(
        FileContent(encoded_file),
        FileName('graph.png'),
        FileType('img/png'),
        Disposition('attachment')
    )

    message.attachment = attachedFile
    sg = SendGridAPIClient(api_key=EMAIL_API_KEY)
    response = sg.send(message)
    print(response.status_code, response.body, response.headers)

def parse_friends(user_id):
    res = requests.get(f"{BASE_URL}/friends.get?user_id={user_id}&fields=name&access_token={ACCESS_TOKEN}&v={API_VERSION}")
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

    data = {'options':f'user id: {user_id}, accuracy: {accuracy}, nodes: {len(graph.nodes)}, edges: {len(graph.edges)}','img':img_data}
    send_email(ADMIN_EMAIL,email,data['options'],data['img'])


def build_graph(user_id, accuracy: float = 1):
    print(f'start parsing (user id={user_id})...')
    mg = nx.DiGraph()
    mg.add_node('Main user')
    main_friends = parse_friends(user_id)['response']['items']
    friends_of_friend_dict = {}
    for friend in main_friends:
        mg.add_node(friend['first_name'] + friend['last_name'])
        mg.add_edge(friend['first_name'] + friend['last_name'], 'Main user')
        try:
            friends_of_friend = parse_friends(friend['id'])['response']['items']
            friends_of_friend_dict[friend['first_name'] + friend['last_name']] = friends_of_friend[:int(len(friends_of_friend)*accuracy)]
        except Exception as e:
            print(e)

    for user in friends_of_friend_dict:
        for friend in friends_of_friend_dict[user]:
            mg.add_node(friend['first_name'] + friend['last_name'])
            mg.add_edge(friend['first_name'] + friend['last_name'], user)

    return mg


def get_random_filename():
    return str(round(time.time() * (10 ** 6))) + str(random.randint(0, 10 ** 7))


def draw_graph(g, filename):
    print('drawing graph...')
    plt.figure(figsize=(26,26))
    nx.draw_random(g, node_size=50, font_size=3, with_labels=True, font_weight='bold')
    plt.savefig(f'images/{filename}.png',dpi=220)
    plt.clf()


@app.get("/")
async def root():
    with open('index.html') as file:
        html = file.read()
    return HTMLResponse(content=html, status_code=200)


@app.get("/graph/user_id={user_id}&email={email}")
async def graph(background_tasks: BackgroundTasks,
                user_id: int = Path(None, title="ID of the Vk user", gt=0),
                email: str = Path(None, max_length=50),
                accuracy: float = Query(1.0, ge=0.0, le=1.0)):
    try:
        validate_email(email)
        background_tasks.add_task(process_request, user_id, accuracy, email)
        return Response(json.dumps({'Answer': 'Your request accepted, we will send result to your email'}))
    except EmailNotValidError as e:
        return Response(str(e), status_code=400)
    except Exception as e:
        return Response(str(e), status_code=500)