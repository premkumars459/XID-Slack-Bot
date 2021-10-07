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
import json

load_dotenv()

app = Flask(__name__)

# ---- Initialization ----
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET_'], '/slack/events', app)
client = slack.WebClient(token=os.environ['SLACK_TOKEN_'])
BOT_ID = client.api_call("auth.test")['user_id']

# ---- Restart Ack ----
client.chat_postMessage(channel='#test_channel', text="restart")

# ---- REGEX ----
PAYOUT_REGEX = f"<@{BOT_ID}> GET_PAYOUT \w*"
FAV_REGEX = f"<@{BOT_ID}> GET_FAV \w*"
PAYOUT_STATUS_REGEX = f"<@{BOT_ID}> GET_PAYOUT_STATUS \w*"
COMMANDS = F"<@{BOT_ID}>$"

# ---- Constants ----
BASE_URL= "https://api-dark.razorpay.com/v1"
key = 'rzp_live_VdaE7NEl1NM0YC'
secret = '5SGIyGLto1oiFBF8SDLd7pZw'

# ---- Command List ----


@slack_event_adapter.on('app_mention')
def handle_mention(payload):
    print(json.dumps(payload))
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    
    if user_id != None and BOT_ID == user_id:
        return

    command, entityId = get_entity_id_and_type(event)
    if command:
        response = get_entity_status(command, entityId)
        client.chat_postMessage(channel=channel_id, text=response)

    else:
        client.chat_postMessage(channel=channel_id, text='I heard you')

def get_entity_status(command, entityId):
    commands = {
        "ALL_AVAILABLE_COMMANDS": get_all_available_commands,
        "GET_PAYOUT": get_payout_details,
        "GET_FAV": get_fav_status,
        "GET_PAYOUT_STATUS": get_payout_status
    }

    if command == "ALL_AVAILABLE_COMMANDS":
        return get_all_available_commands(commands)

    return commands.get(command)(entityId)

def get_all_available_commands(commands):
    keys = list(commands.keys())

    response = ""
    for x in range(len(keys)):
        print(keys)
        print(x)

        if keys[x] == "ALL_AVAILABLE_COMMANDS":
            continue

        response += f"&gt; {keys[x]}\n"

    response = f"Available commands:\n{response}\n"
    response += "Please Use these commands in order *@TestApp1 <COMMAND> <VALUE>*"

    return response

def get_payout_details(payout_id):
    URL = f"{BASE_URL}/payouts/{payout_id}"
    print(f"Payout URL: {URL}")

    r = requests.get(url = URL, auth = (key, secret)).json()
    status = r.get('status')
    fund_account_id = r.get('fund_account_id')
    amount = r.get('amount')
    r = json.dumps(r, indent=4)

    response = f"Payout\n&gt;ID: *{payout_id}*\n&gt;Status: *{status}*\n&gt;Fund Account ID: *{status}*\n&gt;Amount: *{amount}*\nPayout Details\n"
    response = response + "```" + r + "```"
    
    return response

def get_fav_status(fav_id):
    URL = f"{BASE_URL}/fund_accounts/validations/{fav_id}"
    print(f"FAV URL: {URL}")

    r = requests.get(url = URL, auth = (key, secret)).json()
    response = json.dumps(r, indent=4)
    response = "```" + response + "```"
    
    return response

def get_payout_status(payout_id):
    URL = f"{BASE_URL}/payouts/{payout_id}"
    print(f"Payout URL: {URL}")

    r = requests.get(url = URL, auth = (key, secret)).json()
    status = r.get('status')

    response = f"Payout\n&gt;ID: *{payout_id}*\n&gt;Status: *{status}*"
    return response

def get_entity_id_and_type(event):
    text = str(event.get('text'))
    text = text.replace(u'\xa0', u' ')
    print(f"TEXT Extracted: {text}")

    if match_commands_regex(text):
        matches = match_commands_regex(text)
        prefix = f"<@{BOT_ID}> COMMANDS"
        return 'ALL_AVAILABLE_COMMANDS', ''

    elif match_payout_regex(text):
        matches = match_payout_regex(text)
        prefix = f"<@{BOT_ID}> GET_PAYOUT "
        return 'GET_PAYOUT', matches[0][len(prefix):]

    elif match_fav_regex(text):
        matches = match_fav_regex(text)
        prefix = f"<@{BOT_ID}> GET_FAV "
        return 'GET_FAV', matches[0][len(prefix):]

    elif match_payout_status_regex(text):
        matches = match_payout_status_regex(text) 
        prefix = f"<@{BOT_ID}> GET_PAYOUT_STATUS "
        return 'GET_PAYOUT_STATUS', matches[0][len(prefix):]

    else:
        return 'ALL_AVAILABLE_COMMANDS', ''

    return '', ''

# ---- Regex Matching functions ----
def match_commands_regex(text):
    return re.findall(COMMANDS, text)

def match_payout_status_regex(text):
    return re.findall(PAYOUT_STATUS_REGEX, text)

def match_payout_regex(text):
    return re.findall(PAYOUT_REGEX, text)

def match_fav_regex(text):
    return re.findall(FAV_REGEX, text)

if __name__ == "__main__":
    app.run(debug=True)


