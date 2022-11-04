from fastapi import Body, FastAPI, Request, Response, status
from urllib.parse import unquote
from slack_sdk import WebClient
from typing import List
from dotenv import load_dotenv
import os
import re
from datetime import datetime
import pytz
import json

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
    print(command_data)
    data_dict = get_command_data(command_data)
    channels_users = get_channels_and_users(data_dict["text"])
    message = get_message(data_dict["text"])
    for entity in channels_users:
        if entity[0] == "#":
            channels_members = client.conversations_members(channel=entity[1])
            for member in channels_members["members"]:
                client.chat_postMessage(channel=member, text=message, as_user=True)
        else:
            client.chat_postMessage(channel=entity[1], text=message, as_user=True)
    return {"Status": "Success"}


@app.post("/message_schedule")
async def schedule_message(request: Request, response: Response, data=Body(...)):
    raw_body = await request.body()
    body = raw_body.decode("utf-8")
    command_data = [unquote(text) for text in body.split("&")]

    data_dict = get_command_data(command_data)
    channels_users = get_channels_and_users(data_dict["text"])
    message = get_message(data_dict["text"])
    print(message)
    date_time = re.findall(r"\d{1,2}/\d{1,2}/\d{2} \d{1,2}:\d{0,2}:\d{0,2}", message)[0]
    time_epoch = datetime.strptime(date_time, r"%m/%d/%y %H:%M:%S").timestamp()

    for entity in channels_users:
        if entity[0] == "#":
            channels_members = client.conversations_members(channel=entity[1])
            for member in channels_members["members"]:
                client.chat_scheduleMessage(
                    channel=member, text=message, post_at=time_epoch
                )
        else:
            client.chat_scheduleMessage(
                channel=entity[1], text=message, post_at=time_epoch
            )
    return {"Status": "Success"}


@app.post("/message_schdedule_tz")
async def schedule_message_in_user_timzone(
    request: Request, response: Response, data=Body(...)
):
    raw_body = await request.body()
    body = raw_body.decode("utf-8")
    command_data = [unquote(text) for text in body.split("&")]

    data_dict = get_command_data(command_data)
    channels_users = get_channels_and_users(data_dict["text"])
    message = get_message(data_dict["text"])
    date_time = datetime.strptime(
        re.findall(r"\d{1,2}/\d{1,2}/\d{2} \d{1,2}:\d{0,2}:\d{0,2}", message)[0]
    )

    for entity in channels_users:
        if entity[0] == "#":
            channels_members = client.conversations_members(channel=entity[1])
            for member in channels_members["members"]:
                user_tz = client.users_info(member)["tz"]
                convtd_date_time = date_time.astimezone(pytz.timezone(user_tz))
                time_epoch = convtd_date_time.timestamp()
                client.chat_scheduleMessage(
                    channel=member, text=message, post_at=time_epoch
                )
        else:
            user_tz = client.users_info(entity[1])["tz"]
            convtd_date_time = date_time.astimezone(pytz.timezone(user_tz))
            time_epoch = convtd_date_time.timestamp()
            client.chat_scheduleMessage(
                channel=entity[1], text=message, post_at=time_epoch
            )
    return {"Status": "Success"}


@app.post("/shortcut-test")
async def schedule_message_in_user_timzone(
    request: Request, response: Response, data=Body(...)
):
    raw_body = await request.body()
    raw_form = await request.form()
    body = unquote(raw_body.decode("utf-8"))
    payload = json.loads(raw_form.get("payload"))
    resp = client.views_open(
        trigger_id=payload["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "modal-id",
            "title": {"type": "plain_text", "text": "Awesome Modal"},
            "submit": {"type": "plain_text", "text": "Submit"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "b-id",
                    "label": {
                        "type": "plain_text",
                        "text": "Input label",
                    },
                    "element": {
                        "action_id": "a-id",
                        "type": "plain_text_input",
                    },
                }
            ],
        },
    )
    if (
        payload["type"] == "view_submission"
        and payload["view"]["callback_id"] == "modal-id"
    ):
        # Handle a data submission request from the modal
        submitted_data = payload["view"]["state"]["values"]
    return status.HTTP_200_OK
