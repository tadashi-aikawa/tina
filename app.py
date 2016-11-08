# -*- coding: utf-8 -*-

import json
import re

from dateutil import parser
from datetime import datetime, timedelta

import boto3
from pydash import py_
from chalice import Chalice
from pytz import timezone

from chalicelib import api

# Set your environmental parameters
REGION = 'ap-northeast-1'
BUCKET = 'mamansoft-tina'
KEY = '.tinaconfig'

S3 = boto3.client('s3', region_name=REGION)
app = Chalice(app_name='tina')
app.debug = True


@app.route('/ping')
def ping():
    return {'result': 'I am TINA♥'}

# ------------------------
# parse
# ------------------------

def to_project_id(project_by_id, toggl_project_id):
    return py_.find_key(project_by_id,
                        lambda x: toggl_project_id and x.get("toggl_id") == toggl_project_id)


def to_project_name(project_by_id, toggl_project_id):
    p = py_.find(project_by_id,
                 lambda x: toggl_project_id and x.get("toggl_id") == toggl_project_id)
    return p["name"] if p else "No Project"


def to_status(task_pid, task_name, completed_tasks, uncompleted_tasks, interrupted_tasks):
    def to_identify(id, name):
        return u"{}{}".format(id, name)

    completed_task_identifies = py_.map(
        completed_tasks,
        lambda x: to_identify(x['project_id'], x['name'])
    )
    uncompleted_task_identifies = py_.map(
        uncompleted_tasks,
        lambda x: to_identify(x['project_id'], x['name'])
    )
    interrupted_task_identifies = py_(interrupted_tasks) \
        .map(lambda x: py_.find(completed_tasks + uncompleted_tasks, lambda y: x["object_id"] == y["id"])) \
        .filter() \
        .map(lambda x: to_identify(x['project_id'], x['name'])) \
        .value()

    target = to_identify(task_pid, task_name)

    if target in completed_task_identifies and target not in interrupted_task_identifies:
        return "task_completed"
    elif target in uncompleted_task_identifies and target not in interrupted_task_identifies:
        return "task_not_completed"
    elif target in completed_task_identifies and target in interrupted_task_identifies:
        return "interrupted_task_completed"
    elif target in uncompleted_task_identifies and target in interrupted_task_identifies:
        return "interrupted_task_not_completed"
    else:
        # Todoist does not has the task
        return "interrupted_task_completed"

# ------------------------
# utility
# ------------------------


def minus3h(dt):
    return dt - timedelta(hours=3)


def fetch_next_item(config):
    def equal_now_day(utcstr):
        if not utcstr:
            return False
        x = parser.parse(utcstr).astimezone(timezone(config['timezone']))
        now = datetime.now(timezone(config['timezone']))
        # 3:00 - 3:00
        return minus3h(x).date() == minus3h(now).date()

    next_task = py_(api.fetch_uncompleted_tasks(config['todoist']['api_token'])) \
        .filter(lambda x: equal_now_day(x['due_date_utc'])) \
        .sort_by_all(['priority', 'day_order'], [False, True]) \
        .find(lambda x: str(x['project_id']) in config['project_by_id'].keys()) \
        .value()
    if not next_task:
        return None

    next_project_id = next_task['project_id']
    next_project = config['project_by_id'].get(str(next_project_id))
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
    toggl_reports = api.access_toggl(
        '/details?workspace_id={}&since={}&user_agent=tina'.format(
            config['toggl']['workspace'], minus3h(now).strftime('%Y-%m-%d')
        ),
        config['toggl']['api_token'],
        True
    ).json()['data']

    # todoist
    complete_todoist_tasks = py_.map(
        api.fetch_completed_tasks(config['todoist']['api_token'], minus3h(now).replace(hour=0, minute=0, second=0)),
        lambda x: {
            "project_id": x["project_id"],
            "id": x["task_id"],
            "name": x["content"].split(" @")[0],
            "label_names": x["content"].split(" @")[1:],
            "completed_date": parser.parse(x["completed_date"]),
            "private": config['label_by_name']['private']['name'] in x["content"].split(" @")[1:]
        }
    )
    uncompleted_todoist_tasks = py_.map(
        api.fetch_uncompleted_tasks(config['todoist']['api_token']),
        lambda x: {
            "project_id": x["project_id"],
            "id": x["id"],
            "name": x["content"],
            "label_ids": x["labels"],
            "private": config['label_by_name']['private']['id'] in x["labels"]
        }
    )

    # Interrupted task
    work_start_task = py_.find(complete_todoist_tasks,
                               lambda x: x["id"] == config["special_events"]["start-work"]["id"])
    interrupted_tasks = py_.filter(
        api.fetch_activities(config['todoist']['api_token'],
                            '["item:added"]',
                            minus3h(now).replace(hour=0, minute=0, second=0)),
        lambda x: parser.parse(x["event_date"]) > work_start_task["completed_date"]
    )

    def find_todoist_task(project_id, name):
        return py_.find(
            complete_todoist_tasks + uncompleted_todoist_tasks,
            lambda t: project_id == t["project_id"] and name == t["name"]
        )

    def reports2task(reports):
        r = reports[0]
        project_id = to_project_id(config["project_by_id"], r["pid"])
        project_name = to_project_name(config["project_by_id"], r["pid"])
        todoist_task = find_todoist_task(project_id, r["description"])
        return {
            "name": ":secret:" if todoist_task and todoist_task["private"] else r["description"],
            "project_id": project_id,
            "project_name": project_name,
            "elapsed": py_.sum(reports, "dur") / 1000 / 60,
            "status": to_status(
                to_project_id(config["project_by_id"], r["pid"]),
                r["description"],
                complete_todoist_tasks,
                uncompleted_todoist_tasks,
                interrupted_tasks
            )
        }

    return py_(toggl_reports) \
        .group_by(lambda x: u"{}{}".format(x["description"], x["pid"])) \
        .map_values(reports2task) \
        .filter("name") \
        .sort_by(reverse=True) \
        .value()


# ------------------------
# exec
# ------------------------

def exec_remind(entity, config):
    r = api.notify_slack(
        u"@{}\n もうすぐ *{}* の時間だよ".format(config['slack']['mention'], entity['content']),
        config
    )
    return True


def exec_added(entity, config):
    times = re.compile('\d\d:\d\d').findall(entity['content'])
    if times:
        hour, minute = times[0].split(':')
        begin_time = minus3h(datetime.now(timezone(config['timezone']))).replace(hour=int(hour), minute=int(minute), second=0)
        r = api.add_reminder(
            config['todoist']['api_token'],
            entity['id'],
            begin_time - timedelta(minutes=config['remind_minutes_delta'])
        )
        if not r:
            return False

    api.notify_slack(config['message_format_by_event'][entity['event']].format(**entity), config)
    return True


def exec_completed(entity, config):
    special_event = py_.find(config['special_events'], lambda x: x['id'] == entity['id'])
    if special_event:
        # TODO: Create independent function
        api.notify_slack(py_.sample(special_event['messages']), config)
        if special_event == config['special_events']['leave-work']:
            api.notify_slack(
                "\n".join(py_.map(
                    create_daily_report(config),
                    lambda x: config["daily_report_format_by_status"][x["status"]].format(**x)
                )),
                config
            )
    else:
        next_item = fetch_next_item(config)
        next_message = config['next_message_format'].format(**next_item) if next_item is not None else ''
        message = config['message_format_by_event'][entity['event']].format(**entity) + '\n' + next_message
        r = api.notify_slack(message, config)

    # Toggl action
    current_entry = api.access_toggl('/time_entries/current', config['toggl']['api_token']).json()['data']
    if not current_entry or current_entry['description'] != entity['content']:
        return True

    api.access_toggl('/time_entries/{}/stop'.format(current_entry['id']), config['toggl']['api_token'])
    return True


def exec_todoist(config, body):
    item = body["event_data"] if body['event_name'] != "reminder:fired" else \
        py_.find(api.fetch_uncompleted_tasks(config['todoist']['api_token']),
                 lambda x: x['id'] == body["event_data"]['item_id'])

    project = config['project_by_id'].get(str(item['project_id']))
    labels = item['labels']
    private = config['label_by_name']['private']['id'] in labels
    entity = {
        "event": body['event_name'],
        "id": item["id"],
        "project_id": item['project_id'],
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
    elif body['event_name'] == 'item:added':
        return exec_added(entity, config)
    else:
        r = api.notify_slack(config['message_format_by_event'][entity['event']].format(**entity), config)
        return True


@app.route('/todoist', methods=['POST'])
def todoist():
    s3_obj = S3.get_object(Bucket=BUCKET, Key=KEY)
    config = json.loads(s3_obj['Body'].read())
    body = app.current_request.json_body

    return {'is_success': exec_todoist(config, body)}
