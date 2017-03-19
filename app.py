# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import datetime, timedelta

import re
import boto3
from chalice import Chalice
from dateutil import parser
from owlmixin.owlcollections import TList, TDict
from owlmixin.util import O
from pydash import py_
from pytz import timezone
from typing import List, Text, Any, Dict, Tuple

from chalicelib import api
from chalicelib.models import *
from fn import _

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
    # type: (TaskReport, DailyReportFormat) -> Text
    status = daily_report.status  # type: Status
    return ":{}: {}".format(
        report_format.icon.completed if status == Status.COMPLETED \
            else report_format.icon.uncompleted if status == Status.IN_PROGRESS \
            else report_format.icon.re_scheduled if status == Status.RE_SCHEDULED \
            else report_format.icon.removed if status == Status.REMOVED \
            else report_format.icon.not_start_yet if status == Status.NOT_STARTED_YET \
            else report_format.icon.waiting,
        report_format.base.format(
            name=daily_report.name,
            project_name=daily_report.project_name,
            elapsed=daily_report.elapsed or '',
            estimate=daily_report.estimate or '',
            lag="{:+}".format(daily_report.elapsed - daily_report.estimate)
                if daily_report.estimate and daily_report.elapsed else ''
        )
    )


def to_project_id(project_by_id, toggl_project_id):
    # type: (TDict[ProjectId, Project], ProjectId) -> ProjectId
    return py_.find_key(project_by_id, lambda x: toggl_project_id and x.toggl_id == toggl_project_id)


def to_project_name(project_by_id, toggl_project_id):
    # type: (TDict[ProjectId, Project], ProjectId) -> Text
    p = project_by_id.find(lambda k, v: toggl_project_id and v.toggl_id == toggl_project_id)  # type: Project
    return p.name if p else "No Project"


# ------------------------
# utility
# ------------------------

def in_special_events(config, task_id):
    # type: (Config, int) -> bool
    return task_id in [v['id'] for k, v in config.special_events.to_dict().items()]


def is_valid_project(config, project_id):
    # type: (Config, int) -> bool
    return project_id in config.project_by_id.keys()


def is_measured_project(config, project_id):
    # type: (Config, int) -> bool
    return is_valid_project(config, project_id) and config.project_by_id[project_id].toggl_id is not None


def now(tz):
    # type: (Text) -> datetime
    return datetime.now(timezone(tz))


def minus3h(dt):
    # type: (datetime) -> datetime
    return dt - timedelta(hours=3)


def to_datetime(utcstr, tz):
    # type: (Text, Text) -> datetime
    return parser.parse(utcstr).astimezone(timezone(tz))


def equal_now_day(utcstr, tz):
    # type: (Text, Text) -> bool
    if not utcstr:
        return False

    x = to_datetime(utcstr, tz)

    # 3:00 - 3:00
    return minus3h(x).date() == minus3h(now(tz)).date()


def fetch_next_item(config):
    # type: (Config) -> any
    next_task = api.fetch_uncompleted_tasks(config.todoist.api_token) \
        .filter(lambda x: equal_now_day(x.due_date_utc, config.timezone)) \
        .reject(lambda x: config.special_labels.waiting.id in x.labels) \
        .order_by(_.day_order) \
        .order_by(_.priority, reverse=True) \
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


def toggl_to_task_report(config, toggls, todoist_reports):
    # type: (TList[TogglApiReport]) -> TList[TaskReport]

    def toggl_to_report(toggl):
        # type: (TogglApiReport) -> TaskReport
        return todoist_reports.find(
            _.project_id == to_project_id(config.project_by_id, toggl.pid) and \
            _.name_without_emoji == toggl.description_without_emoji
        )

    toggl = toggls[0]
    report = toggl_to_report(toggl)
    return TaskReport.from_dict({
        "id": report.id if report else -1,
        "name": report.name if report else toggl.description,
        "project_id": to_project_id(config.project_by_id, toggl.pid),
        "project_name": to_project_name(config.project_by_id, toggl.pid),
        "is_waiting": report.is_waiting if report else False,
        "elapsed": sum([x.dur / 1000 / 60 for x in toggls])
    })


def create_daily_report(config):
    # type: (Config) -> Tuple[TList[TaskReport], TList[TaskReport]]

    # todoist
    completed_todoist_reports = api.fetch_completed_tasks(
        config.todoist.api_token, minus3h(now(config.timezone)).replace(hour=0, minute=0, second=0)
    ).map(lambda x: TaskReport.from_dict({
        "id": x["task_id"],
        "name": x["content"].split(" @")[0],
        "project_id": x["project_id"],
        "project_name": O(config.project_by_id.get(x["project_id"])).then(_.name).or_("なし"),
        "is_waiting": config.special_labels.waiting.name in x["content"].split(" @")[1:],
        "completed_date": x["completed_date"],
        "estimate": O(
            config.special_labels.estimates.find(lambda l: l.name in x["content"].split(" @")[1:])
        ).then_or_none(_.value)
    })).filter(lambda x: is_measured_project(config, x.project_id))
    """:type: TList[TaskReport]"""

    uncompleted_todoist_reports = api.fetch_uncompleted_tasks(config.todoist.api_token) \
        .map(lambda x: TaskReport.from_dict({
            "id": x.id,
            "name": x.content,
            "project_id": x.project_id,
            "project_name": O(config.project_by_id.get(x.project_id)).then(_.name).or_("なし"),
            "is_waiting": config.special_labels.waiting.id in x.labels,
            "due_date_utc": x.due_date_utc,
            "estimate": O(
                config.special_labels.estimates.find(lambda l: l.id in x.labels)
            ).then_or_none(_.value)
        })).filter(lambda x: is_measured_project(config, x.project_id))
    """:type: TList[TaskReport]"""

    # toggl
    toggl_reports = api.fetch_reports(workspace_id=config.toggl.workspace,
                                     since=minus3h(now(config.timezone)),
                                     api_token=config.toggl.api_token) \
        .group_by(_.task_uniq_key) \
        .to_values() \
        .map(lambda xs: toggl_to_task_report(config, xs, completed_todoist_reports + uncompleted_todoist_reports))
    """:type: TList[TaskReport]"""

    work_start_date = completed_todoist_reports \
        .find(_.id == config.special_events.start_work.id) \
        .completed_date
    """:type: datetime"""

    # ---
    s3_obj = S3.get_object(Bucket=BUCKET, Key=SCHEDULED_TASKS)
    # The task completed before scheduling is the scheduled
    done_before_scheduled = toggl_reports \
        .filter(lambda x: completed_todoist_reports.find(_.id == x.id)) \
        .filter(lambda x: completed_todoist_reports.find(_.id == x.id).completed_date <= work_start_date)
    """:type: TList[TaskReport]"""

    scheduled_reports = TodoistApiTask.from_json_to_list(s3_obj['Body'].read()) \
        .map(lambda x: TaskReport.from_dict({
            "id": x.id,
            "name": x.content,
            "project_id": x.project_id,
            "project_name": O(config.project_by_id.get(x.project_id)).then(_.name).or_("なし"),
            "is_waiting": config.special_labels.waiting.id in x.labels,
            "elapsed": O(toggl_reports.find(_.id == x.id)).then(_.elapsed).or_(0),
            "due_date_utc": x.due_date_utc,
            "estimate": O(
                config.special_labels.estimates.find(lambda l: l.id in x.labels)
            ).then_or_none(_.value),
            "status": Status.COMPLETED if x.id in completed_todoist_reports.map(_.id) \
                else Status.REMOVED if not x.id in uncompleted_todoist_reports.map(_.id) \
                else Status.RE_SCHEDULED if to_datetime(x.due_date_utc, config.timezone).day != minus3h(now(config.timezone)).day \
                else Status.WAITING if config.special_labels.waiting.id in x.labels \
                else Status.NOT_STARTED_YET if O(toggl_reports.find(_.id == x.id)).then(_.elapsed).or_(0) == 0 \
                else Status.IN_PROGRESS
            })) \
        .filter(lambda x: is_measured_project(config, x.project_id))
    """:type: TList[TaskReport]"""

    measured_interrupted_reports = toggl_reports \
        .reject(lambda x: x.id in (scheduled_reports + done_before_scheduled).map(_.id))
    """:type: TList[TaskReport]"""
    unmeasured_interrupted_reports = uncompleted_todoist_reports \
        .filter(lambda x: equal_now_day(x.due_date_utc, config.timezone)) \
        .reject(lambda x: x.id in measured_interrupted_reports.map(_.id)) \
        .reject(lambda x: x.id in (scheduled_reports + done_before_scheduled).map(_.id))
    """:type: TList[TaskReport]"""

    interrupted_reports = (measured_interrupted_reports + unmeasured_interrupted_reports) \
        .map(lambda x: TaskReport.from_dict({
            "id": x.id,
            "name": x.name,
            "project_id": x.project_id,
            "project_name": x.project_name,
            "is_waiting": x.is_waiting,
            "elapsed": x.elapsed,
            "completed_date": x.completed_date,
            "due_date_utc": x.due_date_utc,
            "estimate": x.estimate,
            "status": Status.COMPLETED if x.id in completed_todoist_reports.map(_.id) \
                else Status.COMPLETED if not x.id in uncompleted_todoist_reports.map(_.id) \
                else Status.WAITING if x.is_waiting \
                else Status.NOT_STARTED_YET if x.elapsed == 0 \
                else Status.IN_PROGRESS
        }))

    return scheduled_reports, interrupted_reports


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
        target_time = O(entity.due_date_utc) \
            .then(lambda d: to_datetime(d, config.timezone)) \
            .or_(datetime.now(timezone(config.timezone)))
        begin_time = minus3h(target_time).replace(hour=int(hour), minute=int(minute), second=0)
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
    if entity.in_history and entity.parent_id:
        return True

    special_event = config.special_events.find_by_id(entity.id)  # type: Event
    if special_event:
        # TODO: Create independent function
        api.notify_slack(py_.sample(special_event.messages), config)
        if special_event == config.special_events.leave_work:
            scheduled, interrupted = create_daily_report(config)  # type: TList[TaskReport]
            report_message = """
:spiral_calendar_pad: *朝に予定したタスク* `{total_scheduled}時間`

{scheduled}


:ikiro: *割り込みで入ったタスク* `{total_interrupted}時間`

{interrupted}
            """.format(
                total_scheduled=round(scheduled.sum_by(_.elapsed) / 60.0, 1),
                total_interrupted=round(interrupted.sum_by(_.elapsed) / 60.0, 1),
                scheduled=scheduled.map(lambda r: to_report_string(r, config.daily_report_format)).join("\n"),
                interrupted=interrupted.map(lambda r: to_report_string(r, config.daily_report_format)).join("\n"),
            )
            api.notify_slack(report_message, config)
        elif special_event == config.special_events.start_work:
            scheduled_tasks = api.fetch_uncompleted_tasks(config.todoist.api_token) \
                .filter(lambda x: equal_now_day(x.due_date_utc, config.timezone)) \
                .filter(lambda x:
                        is_valid_project(config, x.project_id) or
                        in_special_events(config, x.id)
                        ) \
                .order_by(_.day_order) \
                .order_by(_.priority, reverse=True)
            """:type: TList[TodoistApiTask]"""

            S3.put_object(Bucket=BUCKET, Key=SCHEDULED_TASKS,
                          Body=scheduled_tasks.reject(lambda x: in_special_events(config, x.id)).to_json())

            api.notify_slack(
                scheduled_tasks.map(lambda x:
                                    config.morning_report_format.base.format(
                                        name=x.content,
                                        project_name=O(config.project_by_id.get(x.project_id)).then(_.name).or_("節目"),
                                        estimate_label=O(
                                            config.special_labels.estimates.find(lambda l: l.id in x.labels)
                                        ).then(_.name).or_('----')
                                    )) \
                .join("\n"),
                config
            )
    else:
        next_item = fetch_next_item(config)
        next_message = config.next_message_format.format(**next_item) if next_item is not None else ''
        message = config.message_format_by_event[entity.event].format(**entity.to_dict()) + '\n' + next_message
        api.notify_slack(message, config)

    # Toggl action
    current_entry = api.access_toggl('/time_entries/current', config.toggl.api_token).json()['data']
    if not current_entry or current_entry['description'] != entity.content_without_emoji:
        return True

    api.access_toggl('/time_entries/{}/stop'.format(current_entry['id']), config.toggl.api_token)
    return True


def exec_todoist(config, body):
    # type: (Config, Any) -> bool
    item = TodoistApiTask.from_dict(body["event_data"]) \
        if body['event_name'] != "reminder:fired" \
        else api.fetch_uncompleted_tasks(config.todoist.api_token) \
        .find(_.id == body["event_data"]['item_id'])

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
        "in_history": item.in_history,
        "due_date_utc": item.due_date_utc
    })

    if not entity.project_name and not in_special_events(config, entity.id):
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
