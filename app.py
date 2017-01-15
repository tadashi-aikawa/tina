# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
from datetime import datetime, timedelta

import boto3
from chalice import Chalice
from dateutil import parser
from pydash import py_
from pytz import timezone
from typing import List, Text, Any, Dict

from chalicelib import api
from chalicelib.models import *

# Set your environmental parameters
REGION = 'ap-northeast-1'
BUCKET = 'mamansoft-tina'
KEY = '.tinaconfig'
SCHEDULED_TASKS = 'scheduled-tasks'

S3 = boto3.client('s3', region_name=REGION)
app = Chalice(app_name='tina')
app.debug = True


@app.route('/ping')
def ping():
    return {'result': 'I am TINA♥'}


# ------------------------
# parse
# ------------------------

def to_report_string(daily_report, report_format):
    # type: (Any, DailyReportFormat) -> Text
    s = daily_report['status']  # type: DailyReportStatus
    return ":{}::{}: {}".format(
        report_format.icon.interrupted if s.is_interrupted else report_format.icon.empty,
        report_format.icon.completed if s.status == Status.COMPLETED \
            else report_format.icon.uncompleted if s.status == Status.IN_PROGRESS \
            else report_format.icon.waiting,
        report_format.base.format(**daily_report)
    )


def to_project_id(project_by_id, toggl_project_id):
    # type: (Dict[ProjectId, Project], ProjectId) -> ProjectId
    return py_.find_key(project_by_id,
                        lambda x: toggl_project_id and x.toggl_id == toggl_project_id)


def to_project_name(project_by_id, toggl_project_id):
    # type: (Dict[ProjectId, Project], ProjectId) -> Text
    p = py_.find(project_by_id, lambda x: toggl_project_id and x.toggl_id == toggl_project_id)  # type: Project
    return p.name if p else "No Project"


def to_status(task_pid, task_name, completed_tasks, uncompleted_tasks, interrupted_tasks):
    # type: (int, Text, List[TodoistTask], List[TodoistTask], List[any]) -> DailyReportStatus
    def to_identify(id, name):
        # Remove emoji (ex. -> :fire:)
        return re.sub(r' *:[^:]+: *', '', "{}{}".format(id, name))

    completed_task_identifies = py_.map(
        completed_tasks,
        lambda x: to_identify(x.project_id, x.name)
    )
    uncompleted_task_identifies = py_.map(
        uncompleted_tasks,
        lambda x: to_identify(x.project_id, x.name)
    )
    interrupted_task_identifies = py_(interrupted_tasks) \
        .map(lambda x: py_.find(completed_tasks + uncompleted_tasks, lambda y: x["object_id"] == y.id)) \
        .filter() \
        .map(lambda x: to_identify(x.project_id, x.name)) \
        .value()
    waiting_task_identifies = py_(uncompleted_tasks) \
        .filter(lambda x: x.is_waiting) \
        .map(lambda x: to_identify(x.project_id, x.name)) \
        .value()

    target = to_identify(task_pid, task_name)

    # Warning: repeating tasks sometimes are included both completed_task and uncompleted_task.
    # Order for conditional expression is very important.
    return DailyReportStatus.from_dict({
        "status": Status.WAITING if target in waiting_task_identifies \
            else Status.COMPLETED if target in completed_task_identifies \
            else Status.IN_PROGRESS if target in uncompleted_task_identifies \
            else Status.COMPLETED,
        "is_interrupted": target in interrupted_task_identifies or
                          target not in completed_task_identifies + uncompleted_task_identifies
    })


# ------------------------
# utility
# ------------------------


def minus3h(dt):
    # type: (datetime) -> datetime
    return dt - timedelta(hours=3)


def fetch_next_item(config):
    # type: (Config) -> any
    def equal_now_day(utcstr):
        if not utcstr:
            return False
        x = parser.parse(utcstr).astimezone(timezone(config.timezone))
        now = datetime.now(timezone(config.timezone))
        # 3:00 - 3:00
        return minus3h(x).date() == minus3h(now).date()

    next_task = api.fetch_uncompleted_tasks(config.todoist.api_token) \
        .filter(lambda x: equal_now_day(x.due_date_utc)) \
        .reject(lambda x: config.special_labels.waiting.id in x.labels) \
        .order_by(lambda x: x.day_order) \
        .order_by(lambda x: x.priority, reverse=True) \
        .find(lambda x: x.project_id in config.project_by_id.keys())
    """:type: TodoistApiTask"""
    if not next_task:
        return None

    next_project_id = next_task.project_id
    next_project = config.project_by_id.get(next_project_id)
    labels = next_task.labels

    return {
        "project_id": next_project_id,
        "project_name": next_project and next_project.name,
        "labels": labels,
        "content": next_task.content
    }


def create_daily_report(config):
    # type: (Config) -> Any
    now = datetime.now(timezone(config.timezone))

    # toggl
    toggl_reports = api.access_toggl(
        '/details?workspace_id={}&since={}&user_agent=tina'.format(
            config.toggl.workspace, minus3h(now).strftime('%Y-%m-%d')
        ),
        config.toggl.api_token,
        True
    ).json()['data']

    # todoist
    complete_todoist_tasks = py_.map(
        api.fetch_completed_tasks(config.todoist.api_token, minus3h(now).replace(hour=0, minute=0, second=0)),
        lambda x: TodoistTask.from_dict({
            "project_id": x["project_id"],
            "id": x["task_id"],
            "name": x["content"].split(" @")[0],
            "is_waiting": config.special_labels.waiting.name in x["content"].split(" @")[1:],
            "completed_date": x["completed_date"]
        })
    )

    uncompleted_todoist_tasks = py_.map(
        api.fetch_uncompleted_tasks(config.todoist.api_token),
        lambda x: TodoistTask.from_dict({
            "project_id": x.project_id,
            "id": x.id,
            "name": x.content,
            "is_waiting": config.special_labels.waiting.id in x.labels
        })
    )

    # Interrupted task
    work_start_task = py_.find(complete_todoist_tasks,
                               lambda x: x.id == config.special_events.start_work.id)
    interrupted_tasks = py_.filter(
        api.fetch_activities(config.todoist.api_token,
                             '["item:added"]',
                             minus3h(now).replace(hour=0, minute=0, second=0)),
        lambda x: parser.parse(x["event_date"]) > work_start_task.completed_date
    )

    def reports2task(reports):
        r = reports[0]
        project_id = to_project_id(config.project_by_id, r["pid"])
        project_name = to_project_name(config.project_by_id, r["pid"])

        return {
            "name": r["description"],
            "project_id": project_id,
            "project_name": project_name,
            "elapsed": py_.sum(reports, "dur") / 1000 / 60,
            "status": to_status(
                to_project_id(config.project_by_id, r["pid"]),
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

def exec_other_events(entity, config):
    # type: (Entity, Config) -> bool
    r = api.notify_slack(
        config.message_format_by_event[entity.event].format(**entity.to_dict()),
        config
    )
    return True


def exec_remind(entity, config):
    # type: (Entity, Config) -> bool
    r = api.notify_slack(
        "@{}".format(config.slack.mention) + "\n" + config.remind.message_format.format(**entity.to_dict()),
        config
    )
    return True


def exec_added(entity, config):
    # type: (Entity, Config) -> bool
    times = re.compile('\d{1,2}:\d{2}').findall(entity.content)
    if times:
        hour, minute = times[0].split(':')
        begin_time = minus3h(datetime.now(timezone(config.timezone))).replace(hour=int(hour), minute=int(minute),
                                                                              second=0)
        r = api.add_reminder(
            config.todoist.api_token,
            entity.id,
            begin_time - timedelta(minutes=config.remind.minutes_delta)
        )
        if not r:
            return False

    api.notify_slack(config.message_format_by_event[entity.event].format(**entity.to_dict()), config)
    return True


def exec_completed(entity, config):
    # type: (Entity, Config) -> bool

    # Ignore the task which is child task and closed in past
    if entity.in_history == 1 and entity.parent_id:
        return True

    special_event = config.special_events.find_by_id(entity.id)  # type: Event
    if special_event:
        # TODO: Create independent function
        api.notify_slack(py_.sample(special_event.messages), config)
        if special_event == config.special_events.leave_work:
            api.notify_slack(
                "\n".join(py_.map(
                    create_daily_report(config),
                    lambda r: to_report_string(r, config.daily_report_format)
                )),
                config
            )
    else:
        next_item = fetch_next_item(config)
        next_message = config.next_message_format.format(**next_item) if next_item is not None else ''
        message = config.message_format_by_event[entity.event].format(**entity.to_dict()) + '\n' + next_message
        api.notify_slack(message, config)

    # Toggl action
    current_entry = api.access_toggl('/time_entries/current', config.toggl.api_token).json()['data']
    if not current_entry or current_entry['description'] != entity.content:
        return True

    api.access_toggl('/time_entries/{}/stop'.format(current_entry['id']), config.toggl.api_token)
    return True


def exec_todoist(config, body):
    # type: (Config, Any) -> bool
    item = TodoistApiTask.from_dict(body["event_data"]) \
        if body['event_name'] != "reminder:fired" \
        else py_.find(api.fetch_uncompleted_tasks(config.todoist.api_token),
                      lambda x: x.id == body["event_data"]['item_id'])

    project = config.project_by_id.get(item.project_id)
    labels = item.labels  # type: List[int]

    entity = Entity.from_dict({
        "event": body['event_name'],
        "id": item.id,
        "project_id": item.project_id,
        "project_name": project and project.name,
        "labels": labels,
        "content": item.content,
        "parent_id": item.parent_id,
        "in_history": item.in_history
    })

    if not entity.project_name and entity.id not in py_.map(config.special_events, lambda x: x.id):
        print('There is no project matched project_id {}'.format(entity.project_id))
        return True

    functions_by_event = {
        'reminder:fired': exec_remind,
        'item:completed': exec_completed,
        'item:added': exec_added
    }
    return functions_by_event.get(body["event_name"], exec_other_events)(entity, config)


@app.route('/todoist', methods=['POST'])
def todoist():
    s3_obj = S3.get_object(Bucket=BUCKET, Key=KEY)
    config = Config.from_yaml(s3_obj['Body'].read())  # type: Config
    body = app.current_request.json_body

    return {'is_success': exec_todoist(config, body)}
