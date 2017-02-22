# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
from enum import Enum
from typing import List, Optional, Text
from datetime import datetime
from dateutil import parser

from owlmixin import OwlMixin, TDict, TList

__all__ = [
    'TodoistEvent',
    'LabelName',
    'ProjectId',
    'Status',
    'DailyReportIcons',
    'DailyReportFormat',
    'Entity',
    'Slack',
    'Toggl',
    'Todoist',
    'TogglApiDetail',
    'TogglApiReport',
    'Event',
    'SpecialEvents',
    'Label',
    'SpecialLabels',
    'Project',
    'Config',
    'TodoistApiTask',
    'TaskReport'
]

TodoistEvent = Text
LabelName = Text
ProjectId = int


def remove_emoji(content):
    return re.sub(r':[^:]+?:', '', content).strip()


class Status(Enum):
    COMPLETED = 'completed'
    IN_PROGRESS = 'in_progress'
    NOT_STARTED_YET = 'not_started_yet'
    WAITING = 'waiting'
    RE_SCHEDULED = 're_scheduled'
    REMOVED = 'removed'


class DailyReportIcons(OwlMixin):
    def __init__(self, completed, uncompleted, removed, re_scheduled, waiting, not_start_yet, empty):
        self.completed = completed  # type: Text
        self.uncompleted = uncompleted  # type: Text
        self.removed = removed  # type: Text
        self.re_scheduled = re_scheduled  # type: Text
        self.waiting = waiting  # type: Text
        self.not_start_yet = not_start_yet  # type: Text
        self.empty = empty  # type: Text


class DailyReportFormat(OwlMixin):
    def __init__(self, base, icon):
        self.base = base  # type: Text
        self.icon = DailyReportIcons.from_dict(icon)  # type: DailyReportIcons


class MorningReportFormat(OwlMixin):
    def __init__(self, base):
        self.base = base  # type: Text


class Entity(OwlMixin):
    def __init__(self, event, id, project_id,
                 project_name, labels, content,
                 in_history, parent_id=None, due_date_utc=None):
        self.event = event  # type: Text
        self.id = id  # type: int
        self.project_id = project_id  # type: int
        self.project_name = project_name  # type: Text
        self.labels = TList(labels)  # type: TList[int]
        self.content = content  # type: Text
        self._in_history = in_history  # type: int
        self.parent_id = parent_id  # type: Optional[int]
        self.due_date_utc = due_date_utc  # type: Optional[Text]

    @property
    def content_without_emoji(self):
        return remove_emoji(self.content)

    @property
    def in_history(self):
        # type: () -> bool
        return self._in_history == 1


class Slack(OwlMixin):
    def __init__(self, channel, mention, url, username=None, icon_emoji=None, icon_url=None):
        self.channel = channel  # type: Text
        self.mention = mention  # type: Text
        self.url = url  # type: Text
        self.username = username  # type: Optional[Text]
        self.icon_emoji = icon_emoji  # type: Optional[Text]
        self.icon_url = icon_url  # type: Optional[Text]


class Toggl(OwlMixin):
    def __init__(self, api_token, workspace):
        self.api_token = api_token  # type: Text
        self.workspace = workspace  # type: int


class Todoist(OwlMixin):
    def __init__(self, api_token):
        self.api_token = api_token  # type: Text


class Event(OwlMixin):
    def __init__(self, id, messages):
        self.id = id  # type: int
        self.messages = TList(messages)  # type: TList[Text]


class SpecialEvents(OwlMixin):
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


class Label(OwlMixin):
    def __init__(self, id, name):
        self.id = id  # type: int
        self.name = name  # type: Text


class SpecialLabels(OwlMixin):
    def __init__(self, waiting):
        self.waiting = Label.from_dict(waiting)  # type: Label


class Project(OwlMixin):
    def __init__(self, name, toggl_id=None):
        self.name = name  # type: Text
        self.toggl_id = toggl_id  # type: Optional[int]


class Remind(OwlMixin):
    def __init__(self, minutes_delta, message_format):
        self.minutes_delta = minutes_delta  # type: int
        self.message_format = message_format  # type: Text


class Config(OwlMixin):
    def __init__(self, timezone, remind, slack, toggl, todoist,
                 special_events, message_format_by_event, next_message_format,
                 daily_report_format, morning_report_format, special_labels, project_by_id):
        self.timezone = timezone  # type: Text
        self.remind = Remind.from_dict(remind)  # type: Remind
        self.slack = Slack.from_dict(slack)  # type: Slack
        self.toggl = Toggl.from_dict(toggl)  # type: Toggl
        self.todoist = Todoist.from_dict(todoist)  # type: Todoist
        self.special_events = SpecialEvents.from_dict(special_events)  # type: SpecialEvents
        self.message_format_by_event = TDict(message_format_by_event)  # type: TDict[TodoistEvent, Text]
        self.next_message_format = next_message_format  # type: Text
        self.daily_report_format = DailyReportFormat.from_dict(daily_report_format)  # type: DailyReportFormat
        self.morning_report_format = MorningReportFormat.from_dict(morning_report_format)  # type: MorningReportFormat
        self.special_labels = SpecialLabels.from_dict(special_labels)  # type: SpecialLabels
        self.project_by_id = Project.from_dicts_by_key(project_by_id)  # type: TDict[ProjectId, Project]


class TogglApiReport(OwlMixin):
    def __init__(self, id, description, start, end, updated,
                 dur, use_stop, pid=None, **extra):
        self.id = id  # type: int
        self.pid = pid  # type: Optional[int]
        self.description = description  # type: Text
        self.start = parser.parse(start)  # type: datetime
        self.end = parser.parse(end)  # type: datetime
        self.updated = parser.parse(updated) # type: datetime
        self.dur = dur  # type: int
        self.use_stop = use_stop  # type: bool

    @property
    def task_uniq_key(self):
        return str(self.pid) + self.description


class TogglApiDetail(OwlMixin):
    def __init__(self, total_count, per_page, data, **extra):
        self.total_count = total_count  # type: int
        self.per_page = per_page  # type: int
        self.data = TogglApiReport.from_dicts(data)  # type: TList[TogglApiReport]


class TodoistApiTask(OwlMixin):
    def __init__(self, id, content, priority, project_id, labels, checked,
                 due_date_utc, date_added, date_lang,
                 collapsed, date_string, is_archived, in_history,
                 indent, user_id, is_deleted,
                 day_order=None, item_order=None, due_date=None, all_day=None, parent_id=None, **extra):
        self.id = id  # type: int
        self.content = content  # type: Text
        self.priority = priority  # type: int
        self.project_id = project_id  # type: int
        self.labels = TList(labels)  # type: TList[int]
        self.checked = checked  # type: int

        self.due_date = due_date  # type: Optional[Text]
        self.due_date_utc = due_date_utc  # type: Text
        self.date_added = date_added  # type: Text
        self.date_lang = date_lang  # type: Text
        self.date_string = date_string  # type: Text

        self.day_order = day_order  # type: Optional[int]
        self.item_order = item_order  # type: Optional[int]
        self.parent_id = parent_id  # type: Optional[int]
        self.collapsed = collapsed  # type: int

        self.is_archived = is_archived  # type: int
        self.in_history = in_history  # type: int
        self.indent = indent  # type: int
        self.user_id = user_id  # type: int
        self.is_deleted = is_deleted  # type: int
        self.all_day = all_day  # type: Optional[bool]


class TaskReport(OwlMixin):
    def __init__(self, id, name, project_id, project_name, is_waiting, elapsed=0,
                 completed_date=None, due_date_utc=None, status=None):
        self.id = id  # type: int
        self.name = name  # type: Text
        self.project_id = project_id  # type: int
        self.project_name = project_name  # type: Text
        self.is_waiting = is_waiting  # type: bool
        self.elapsed = elapsed  # type: int
        self.completed_date = completed_date  # type: Optional[datetime]
        self.due_date_utc = due_date_utc  # type: Optional[Text]
        self.status = status  # type: Optional[Status]

    @property
    def name_without_emoji(self):
        return remove_emoji(self.name)
