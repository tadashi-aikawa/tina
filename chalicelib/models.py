# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from enum import Enum
from typing import List, Optional, Dict, Text
from datetime import datetime
from dateutil import parser

from dictmixin.main import DictMixin

__all__ = [
    'TodoistEvent',
    'LabelName',
    'ProjectId',
    'Status',
    'DailyReportStatus',
    'DailyReportIcons',
    'DailyReportFormat',
    'Entity',
    'Slack',
    'Toggl',
    'Todoist',
    'Event',
    'SpecialEvents',
    'Label',
    'SpecialLabels',
    'Project',
    'Config',
    'TodoistApiTask',
    'TodoistTask'
]

TodoistEvent = Text
LabelName = Text
ProjectId = int


class Status(Enum):
    COMPLETED = 'completed'
    IN_PROGRESS = 'in_progress'
    WAITING = 'waiting'


class DailyReportStatus(DictMixin):
    def __init__(self, status, is_interrupted):
        # type: (Status, bool) -> DailyReportStatus
        self.status = status  # type: Status
        self.is_interrupted = is_interrupted  # type: bool


class DailyReportIcons(DictMixin):
    def __init__(self, completed, uncompleted, interrupted, waiting, empty):
        self.completed = completed  # type: Text
        self.uncompleted = uncompleted  # type: Text
        self.interrupted = interrupted  # type: Text
        self.waiting = waiting  # type: Text
        self.empty = empty  # type: Text


class DailyReportFormat(DictMixin):
    def __init__(self, base, icon):
        self.base = base  # type: Text
        self.icon = DailyReportIcons.from_dict(icon)  # type: DailyReportIcons


class Entity(DictMixin):
    def __init__(self, event, id, project_id,
                 project_name, labels, content,
                 parent_id, in_history):
        self.event = event  # type: Text
        self.id = id  # type: int
        self.project_id = project_id  # type: int
        self.project_name = project_name  # type: Text
        self.labels = labels  # type: List[int]
        self.content = content  # type: Text
        self.parent_id = parent_id  # type: Optional[int]
        self.in_history = in_history  # type: int


class Slack(DictMixin):
    def __init__(self, channel, mention, url, icon_emoji=None, icon_url=None):
        self.channel = channel  # type: Text
        self.mention = mention  # type: Text
        self.url = url  # type: Text
        self.icon_emoji = icon_emoji  # type: Optional[Text]
        self.icon_url = icon_url  # type: Optional[Text]


class Toggl(DictMixin):
    def __init__(self, api_token, workspace):
        self.api_token = api_token  # type: Text
        self.workspace = workspace  # type: int


class Todoist(DictMixin):
    def __init__(self, api_token):
        self.api_token = api_token  # type: Text


class Event(DictMixin):
    def __init__(self, id, messages):
        self.id = id  # type: int
        self.messages = messages  # type: List[Text]


class SpecialEvents(DictMixin):
    def __init__(self, start_work, lunch_start, lunch_end,
                 must_task_completed,  leave_work):
        self.start_work = Event.from_dict(start_work)  # type: Event
        self.lunch_start = Event.from_dict(lunch_start)  # type: Event
        self.lunch_end = Event.from_dict(lunch_end)  # type: Event
        self.must_task_completed = Event.from_dict(must_task_completed)  # type: Event
        self.leave_work = Event.from_dict(leave_work)  # type: Event

    def find_by_id(self, _id):
        # type: (int) -> Optional[Event]
        for k, v in self.to_dict().items():
            if v.get("id") == _id:
                return getattr(self, k)

        return None


class Label(DictMixin):
    def __init__(self, id, name):
        self.id = id  # type: int
        self.name = name  # type: Text


class SpecialLabels(DictMixin):
    def __init__(self, waiting):
        self.waiting = Label.from_dict(waiting)  # type: Label


class Project(DictMixin):
    def __init__(self, name, toggl_id=None):
        self.name = name  # type: Text
        self.toggl_id = toggl_id  # type: Optional[int]


class Remind(DictMixin):
    def __init__(self, minutes_delta, message_format):
        self.minutes_delta = minutes_delta  # type: int
        self.message_format = message_format  # type: Text


class Config(DictMixin):
    def __init__(self, timezone, remind, slack, toggl, todoist,
                 special_events, message_format_by_event, next_message_format,
                 daily_report_format, special_labels, project_by_id):
        self.timezone = timezone  # type: Text
        self.remind = Remind.from_dict(remind)  # type: Remind
        self.slack = Slack.from_dict(slack)  # type: Slack
        self.toggl = Toggl.from_dict(toggl)  # type: Toggl
        self.todoist = Todoist.from_dict(todoist)  # type: Todoist
        self.special_events = SpecialEvents.from_dict(special_events)  # type: SpecialEvents
        self.message_format_by_event = message_format_by_event  # type: Dict[TodoistEvent, Text]
        self.next_message_format = next_message_format  # type: Text
        self.daily_report_format = DailyReportFormat.from_dict(daily_report_format)  # type: DailyReportFormat
        self.special_labels = SpecialLabels.from_dict(special_labels)  # type: SpecialLabels
        self.project_by_id = Project.from_dict2dict(project_by_id)  # type: Dict[ProjectId, Project]


class TodoistApiTask(DictMixin):
    def __init__(self, id, content, priority, project_id, labels, checked,
                 due_date_utc, date_added, date_lang,
                 parent_id, collapsed, date_string,
                 assigned_by_uid, is_archived, sync_id, in_history,
                 indent, user_id, is_deleted, responsible_uid,
                 day_order=None, item_order=None, due_date=None, all_day=None):
        self.id = id  # type: int
        self.content = content  # type: Text
        self.priority = priority  # type: int
        self.project_id = project_id  # type: int
        self.labels = labels  # type: List[int]
        self.checked = checked  # type: int

        self.due_date = due_date  # type: Text
        self.due_date_utc = due_date_utc  # type: Text
        self.date_added = date_added  # type: Text
        self.date_lang = date_lang  # type: Text
        self.date_string = date_string  # type: Text

        self.day_order = day_order  # type: int
        self.item_order = item_order  # type: int
        self.parent_id = parent_id  # type: int
        self.collapsed = collapsed  # type: int

        self.assigned_by_uid = assigned_by_uid  # type: int
        self.is_archived = is_archived  # type: int
        self.sync_id = sync_id  # type: int
        self.in_history = in_history  # type: int
        self.indent = indent  # type: int
        self.user_id = user_id  # type: int
        self.is_deleted = is_deleted  # type: int
        self.responsible_uid = responsible_uid  # type: int
        self.all_day = all_day  # type: bool


class TodoistTask(DictMixin):
    def __init__(self, id, name, project_id, is_waiting, completed_date=None):
        # type: (int, Text, int, Dict, Text) -> TodoistTask
        self.id = id  # type: int
        self.name = name  # type: Text
        self.project_id = project_id  # type: int
        self.is_waiting = is_waiting  # type: bool
        if completed_date:
            self.completed_date = parser.parse(completed_date)  # type: datetime
