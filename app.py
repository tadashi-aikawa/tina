# -*- coding: utf-8 -*-

import json
from dateutil import parser
from datetime import datetime

import boto3
import requests
from pydash import py_
from chalice import Chalice
from pytz import timezone, utc

# Set your environmental parameters
REGION = 'ap-northeast-1'
BUCKET = 'mamansoft-tina'
KEY = '.tinaconfig'

TOGGL_API_URL = 'https://www.toggl.com/api/v8'
TOGGL_REPORT_API_URL = 'https://www.toggl.com/reports/api/v2'
TODOIST_API_URL = 'https://todoist.com/API/v7'

S3 = boto3.client('s3', region_name=REGION)
app = Chalice(app_name='tina')
app.debug = True


@app.route('/ping')
def ping():
    return {'result': 'I am TINA♥'}


# ------------------------
# post/get
# ------------------------

def access_toggl(path, api_token, is_report=False):
    url = TOGGL_REPORT_API_URL if is_report else TOGGL_API_URL
    return requests.get(url + path, auth=(api_token, 'api_token'))


def notify_slack(message, config):
    payload = {
        "text": message,
        "username": u"TINA",
        "icon_emoji": config['slack'].get('icon_emoji'),
        "icon_url": config['slack'].get('icon_url'),
        "channel": config['slack'].get('channel'),
        "link_names": 1
    }
    r = requests.post(config['slack']['url'], data=json.dumps(payload, ensure_ascii=False).encode('utf8'))
    # for debug
    print(r.status_code)
    print(r.content)

    return r


def fetch_uncompleted_tasks(todoist_token):
    items = requests.get(TODOIST_API_URL + '/sync', data={
        "token": todoist_token,
        "sync_token": "*",
        "resource_types": '["items"]'
    }).json()['items']
    return py_.reject(items, "checked")


def fetch_completed_tasks(todoist_token, since):
    return requests.get(TODOIST_API_URL + '/completed/get_all', data={
        "token": todoist_token,
        "since": since.astimezone(utc).strftime('%Y-%m-%dT%H:%M'),
        "limit": 50
    }).json()['items']


# ------------------------
# parse
# ------------------------

def to_project_id(project_by_id, toggl_project_id):
    return py_.find_key(project_by_id, lambda x: x.get("toggl_id") == str(toggl_project_id))


def to_project_name(project_by_id, toggl_project_id):
    p = py_.find(project_by_id, lambda x: x.get("toggl_id") == str(toggl_project_id))
    return p["name"] if p else "No Project"


def to_status(task_pid, task_name, completed_tasks, uncompleted_tasks):
    def to_identify(id, name):
        return u"{}{}".format(id, name)

    complete_task_identifies = py_.map(
        completed_tasks,
        lambda x: to_identify(x['project_id'], x['name'])
    )
    todoist_task_identifies = py_.map(
        uncompleted_tasks,
        lambda x: to_identify(x['project_id'], x['content'])
    )
    target = to_identify(task_pid, task_name)

    if target in complete_task_identifies:
        return "task_completed"
    elif target in todoist_task_identifies:
        return "task_not_completed"
    else:
        return "interrupted"

# ------------------------
# utility
# ------------------------

def fetch_next_item(config):
    def equal_now_day(utcstr):
        if not utcstr:
            return False
        x = parser.parse(utcstr).astimezone(timezone(config['timezone']))
        now = datetime.now(timezone(config['timezone']))
        return x.date() == now.date()

    next_task = py_(fetch_uncompleted_tasks(config['todoist']['api_token'])) \
        .filter(lambda x: equal_now_day(x['due_date_utc'])) \
        .sort_by_all(['priority', 'day_order'], [False, True]) \
        .find(lambda x: str(x['project_id']) in config['project_by_id'].keys()) \
        .value()
    if not next_task:
        return None

    next_project_id = str(next_task['project_id'])
    next_project = config['project_by_id'].get(next_project_id)
    labels = next_task['labels']
    private = config['label_by_name']['private']['id'] in labels
    return {
        "project_id": next_project_id,
        "project_name": next_project and next_project.get('name'),
        "labels": next_task['labels'],
        "content": config["secret_name"] if private else next_task['content'],
        "private": private
    }


def create_daily_report(config):
    now = datetime.now(timezone(config['timezone']))

    # toggl
    elasped_tasks = access_toggl(
        '/details?workspace_id={}&since={}&user_agent=tina'.format(
            config['toggl']['workspace'], now.strftime('%Y-%m-%d')
        ),
        config['toggl']['api_token'],
        True
    ).json()['data']

    # todoist
    complete_todoist_tasks = py_.map(
        fetch_completed_tasks(config['todoist']['api_token'], now.replace(hour=0, minute=0, second=0)),
        lambda x: {
            "project_id": x["project_id"],
            "id": x["task_id"],
            "name": x["content"].split(" @")[0],
            "label_names": x["content"].split(" @")[1:],
            "private": config['label_by_name']['private']['name'] in x["content"].split(" @")[1:]
        }
    )
    uncompleted_todoist_tasks = fetch_uncompleted_tasks(config['todoist']['api_token'])

    return py_(elasped_tasks) \
        .group_by(lambda x: u"{}{}".format(x["description"], x["pid"])) \
        .map_values(lambda xs: {
            "task": xs[0]["description"],
            "project_id": to_project_id(config["project_by_id"], xs[0]["pid"]),
            "project_name": to_project_name(config["project_by_id"], xs[0]["pid"]),
            "elapsed": py_.sum(xs, "dur") / 1000 / 60,
            "status": to_status(
                to_project_id(config["project_by_id"], xs[0]["pid"]),
                xs[0]["description"],
                complete_todoist_tasks,
                uncompleted_todoist_tasks
            )
        }) \
        .filter("task") \
        .reject(lambda x: py_.find(
            complete_todoist_tasks,
            lambda c: str(x["project_id"]) == str(c["project_id"]) and x["task"] == c["name"]
        )["private"]) \
        .sort_by(reverse=True) \
        .value()


# ------------------------
# exec
# ------------------------

def exec_remind(entity, config):
    r = notify_slack(
        u"@{}\n もうすぐ *{}* の時間だよ".format(config['slack']['mention'], entity['content']),
        config
    )
    return True


def exec_completed(entity, config):
    special_event = py_.find(config['special_events'], lambda x: x['id'] == entity['id'])
    if special_event:
        # TODO: Create independent function
        notify_slack(py_.sample(special_event['messages']), config)
        if special_event == config['special_events']['leave-work']:
            notify_slack(
                "\n".join(py_.map(
                    create_daily_report(config),
                    lambda x: config["daily_report_format_by_status"][x["status"]].format(**x)
                )),
                config
            )
        return True

    next_item = fetch_next_item(config)
    next_message = config['next_message_format'].format(**next_item) if next_item is not None else ''
    message = config['message_format_by_event'][entity['event']].format(**entity) + '\n' + next_message
    r = notify_slack(message, config)

    # Toggl action
    current_entry = access_toggl('/time_entries/current', config['toggl']['api_token']).json()['data']
    if not current_entry or current_entry['description'] != entity['content']:
        return True

    access_toggl('/time_entries/{}/stop'.format(current_entry['id']), config['toggl']['api_token'])
    return True


def exec_todoist(config, body):
    item = body["event_data"] if body['event_name'] != "reminder:fired" else \
        py_.find(fetch_uncompleted_tasks(config['todoist']['api_token']),
                 lambda x: x['id'] == body["event_data"]['item_id'])

    project_id = str(item['project_id'])
    project = config['project_by_id'].get(project_id)
    labels = item['labels']
    private = config['label_by_name']['private']['id'] in labels
    entity = {
        "event": body['event_name'],
        "id": str(item['id']),
        "project_id": project_id,
        "project_name": project and project.get('name'),
        "labels": labels,
        "content": config["secret_name"] if private else item['content'],
        "private": private
    }

    if not entity['project_name']:
        print('There is no project matched project_id {}'.format(entity['project_id']))
        return True

    if body['event_name'] == 'reminder:fired':
        return exec_remind(entity, config)
    elif body['event_name'] == 'item:completed':
        return exec_completed(entity, config)
    else:
        r = notify_slack(config['message_format_by_event'][entity['event']].format(**entity), config)
        return True


@app.route('/todoist', methods=['POST'])
def todoist():
    s3_obj = S3.get_object(Bucket=BUCKET, Key=KEY)
    config = json.loads(s3_obj['Body'].read())
    body = app.current_request.json_body

    return {'is_success': exec_todoist(config, body)}
