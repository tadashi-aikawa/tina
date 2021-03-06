# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from owlmixin.owlcollections import TList
from typing import Text

import json
import uuid
from pytz import utc
import requests
from datetime import datetime

from chalicelib.models import *
from fn import _

USERNAME_DEFAULT = "TINA"
TOGGL_API_URL = 'https://www.toggl.com/api/v8'
TOGGL_REPORT_API_URL = 'https://www.toggl.com/reports/api/v2'
TODOIST_API_URL = 'https://todoist.com/API/v7'


def fetch_reports(workspace_id, since, api_token):
    # type: (int, datetime, Text) -> TList[TogglApiReport]
    path = '/details?workspace_id={}&since={}&user_agent=tina'.format(
        workspace_id, since.strftime('%Y-%m-%d')
    )
    return TogglApiDetail.from_dict(
        access_toggl(path, api_token, True).json()
    ).data


def access_toggl(path, api_token, is_report=False):
    url = TOGGL_REPORT_API_URL if is_report else TOGGL_API_URL
    return requests.get(url + path, auth=(api_token, 'api_token'))


def notify_slack(message, config):
    # type: (Text, Config) -> any
    payload = {
        "text": message,
        "username": config.slack.username or USERNAME_DEFAULT,
        "icon_emoji": config.slack.icon_emoji,
        "icon_url": config.slack.icon_url,
        "channel": config.slack.channel,
        "link_names": 1
    }
    r = requests.post(config.slack.url, data=json.dumps(payload, ensure_ascii=False).encode('utf8'))
    # for debug
    print(r.status_code)
    print(r.content)

    return r


def fetch_uncompleted_tasks(todoist_token):
    # type: (Text) -> TList[TodoistApiTask]
    items = requests.get(TODOIST_API_URL + '/sync', params={
        "token": todoist_token,
        "sync_token": "*",
        "resource_types": '["items"]'
    }).json()['items']
    return TodoistApiTask.from_dicts(items).reject(_.checked)


def fetch_completed_tasks(todoist_token, since):
    def fetch_all():
        offset = 0
        max_limit = 50

        while True:
            rs = TList(requests.get(TODOIST_API_URL + '/completed/get_all', params={
                "token": todoist_token,
                "since": since.astimezone(utc).strftime('%Y-%m-%dT%H:%M'),
                "offset": offset,
                "limit": max_limit
            }).json()['items'])
            yield rs

            if len(rs) != max_limit:
                break
            offset = offset + max_limit

    return TList(fetch_all()).flatten()


def fetch_activities(todoist_token, object_event_types, since):
    return requests.get(TODOIST_API_URL + '/activity/get', params={
        "token": todoist_token,
        "since": since.astimezone(utc).strftime('%Y-%m-%dT%H:%M'),
        "object_event_types": object_event_types,
        "limit": 100
    }).json()


def add_reminder(todoist_token, item_id, remind_time):
    commands = [{
        "type": "reminder_add",
        "uuid": str(uuid.uuid4()),
        "temp_id": str(uuid.uuid4()),
        "args": {
            "item_id": item_id,
            "service": "push",
            "due_date_utc": remind_time.astimezone(utc).strftime('%Y-%m-%dT%H:%M')
        }
    }]

    r = requests.get(TODOIST_API_URL + '/sync', params={
        "token": todoist_token,
        "commands": json.dumps(commands)
    })

    return r.ok


def update_day_orders(todoist_token, ids):
    commands = [{
        "type": "item_update_day_orders",
        "uuid": str(uuid.uuid4()),
        "args": {
            "ids_to_orders": {x: i+1 for i, x in enumerate(ids)},
        }
    }]

    r = requests.get(TODOIST_API_URL + '/sync', params={
        "token": todoist_token,
        "commands": json.dumps(commands)
    })

    return r.ok
