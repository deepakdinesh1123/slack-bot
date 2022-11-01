from fastapi import Body, FastAPI, Request, Response
from urllib.parse import unquote
from slack_sdk import WebClient
from typing import List
from dotenv import load_dotenv
import os
import re
from datetime import datetime

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


def get_channels_and_users(text: str) -> List[str]:
    channels_users = re.findall(r"<([#@])(.*?)\|(.*?)>", text)
    return channels_users


def get_message(text: str) -> str:
    re_obj = re.compile(r"<[#@].*?\|.*>")
    message = re_obj.sub("", text)
    actual_message = " ".join(message.split("+"))
    return actual_message


@app.post("/message")
async def message_members_channels(
    request: Request, response: Response, data=Body(...)
):
    raw_body = await request.body()
    body = raw_body.decode("utf-8")
    command_data = [unquote(text) for text in body.split("&")]

    data_dict = get_command_data(command_data)
    channels_users = get_channels_and_users(data_dict["text"])
    message = get_message(data_dict["text"])
    for entity in channels_users:
        client.chat_postMessage(channel=entity[1], text=message, as_user=True)

    return {"Status": "Success"}


@app.post("/message_schedule")
async def schedule_message(request: Request, response: Response, data=Body(...)):
    raw_body = await request.body()
    body = raw_body.decode("utf-8")
    command_data = [unquote(text) for text in body.split("&")]

    data_dict = get_command_data(command_data)
    channels = get_channels_and_users(data_dict["text"])
    message = get_message(data_dict["text"])
    print(message)
    date_time = re.findall(r"\d{1,2}/\d{1,2}/\d{2} \d{1,2}:\d{0,2}:\d{0,2}", message)[0]
    time_epoch = datetime.strptime(date_time, r"%m/%d/%y %H:%M:%S").timestamp()
    print(channels)

    for entity in channels:
        client.chat_scheduleMessage(channel=entity[1], text=message, post_at=time_epoch)
    return {"Status": "Success"}
