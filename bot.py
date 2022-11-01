from fastapi import Body, FastAPI, Request, Response
from urllib.parse import unquote
from slack_sdk import WebClient
from typing import List
from dotenv import load_dotenv
import os

load_dotenv(".env")

app = FastAPI()

client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))


def get_command_data(cmd_data: List) -> dict:
    data_dict = {}
    for data in cmd_data:
        try:
            key, value = data.split("=")
        except ValueError:
            continue
        data_dict[key] = value
    return data_dict


@app.post("/message")
async def message_members(request: Request, response: Response, data=Body(...)):
    raw_body = await request.body()
    body = raw_body.decode("utf-8")
    command_data = [unquote(text) for text in body.split("&")]
    data_dict = get_command_data(command_data)
    try:
        members = data_dict["text"].split("+")
    except ValueError:
        members = data_dict["text"]
    team_members = client.users_list()
    member_id_dict = {
        member["name"]: member["id"] for member in team_members["members"]
    }

    for member in members:
        if member[1:] in member_id_dict:
            client.chat_postMessage(channel=member_id_dict[member[1:]], text="Hello")

    return {"Status": "Success"}


@app.post("/message-channels")
async def message_channel(request: Request, response: Response, data=Body(...)):
    raw_body = await request.body()
    body = raw_body.decode("utf-8")
    command_data = [unquote(text) for text in body.split("&")]
    data_dict = get_command_data(command_data)
    print(data_dict)
    try:
        channels = data_dict["text"].split("+")
    except ValueError:
        channels = data_dict["text"]

    for channel_name in channels:
        client.chat_postMessage(channel=channel_name[1:], text="Hello")

    return {"Status": "Success"}
