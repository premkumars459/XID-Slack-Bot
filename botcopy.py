import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
import string
from datetime import datetime, timedelta
import time
import json
import requests
import re

load_dotenv()

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(
    os.environ['SIGNING_SECRET_'], '/slack/events', app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN_'])

# client.chat_postMessage(channel='#test_channel', text="first message")

BOT_ID = client.api_call("auth.test")['user_id']

BASE_URL= "https://api-dark.razorpay.com/v1"
PAYOUT_REGEX = f"<@{BOT_ID}> check payout \S*"
FAV_REGEX = f"<@{BOT_ID}> check fav \S*"

# @slack_event_adapter.on('message')
# def message(payload):
#     event = payload.get('event', {})
#     channel_id = event.get('channel')
#     user_id = event.get('user')
#     text = event.get('text')

#     if user_id != None and BOT_ID != user_id:
#         client.chat_postMessage(channel=channel_id, text = 'I heard it')

@slack_event_adapter.on('app_mention')
def handle_mention(payload):
    print(payload)
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    if user_id != None and BOT_ID == user_id:
        return
    # print(payload['event'])
    
    # client.chat_postMessage(channel=channel_id, text = f'you said: {text}')
    content = json.dumps(event, indent = 4)


    payout_id = get_payout_id(event)
    if payout_id == 'return content':
        # client.chat_postMessage(channel=channel_id, text = f'you said: {text}')
        return
    status_json = check_payout_status(payout_id)
    print(status_json)
    content = json.dumps(status_json, indent=4)
    client.chat_postMessage(channel=channel_id, text = content)

def check_payout_status(payout_id):
    key = 'rzp_live_VdaE7NEl1NM0YC'
    secret = '5SGIyGLto1oiFBF8SDLd7pZw'
    # autherization = f"{key}:{secret}"

    URL = f"{BASE_URL}/payouts/{payout_id}"
    r = requests.get(url = URL, auth = (key, secret))
    return r.json()
    
def get_payout_id(event):
    elements = event['blocks'][0]['elements'][0]['elements']
    text = event.get('text')
    if (len(elements) ==2 ):
        print(elements)
        target = elements[1]
        print(target)
        if (target['type'] == 'text'):
            params = target['text'].split()
            print(params)
            if (len(params) == 2 and params[0] == 'check'):
                return params[1]

    return 'return content'

def get_entity_id(event):
    text = event.get('text')
    if match_payout_regex(text):
        matches = match_payout_regex(text)
        prefix = f"<@{BOT_ID}> check payout "
        return ['payout', matches[0][len(prefix):]]

    elif match_fav_regex(text):
        matches = match_fav_regex(text)
        prefix = f"<@{BOT_ID}> check fav "
        return ['fav', matches[0][len(prefix):]]

    return []

def match_payout_regex(text):
    return re.findall(PAYOUT_REGEX, text)

def match_fav_regex(text):
    return re.findall(FAV_REGEX, text)

if __name__ == "__main__":
    # schedule_messages(SCHEDULED_MESSAGES)
    # ids = list_scheduled_messages('C01BXQNT598')
    # delete_scheduled_messages(ids, 'C01BXQNT598')
    app.run(debug=True)