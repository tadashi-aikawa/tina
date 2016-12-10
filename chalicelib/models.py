# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from typing import List, Optional, Dict, Text
from dictmixin.main import DictMixin

TodoistEvent = Text
LabelName = Text
ProjectId = int

"""
* task_completed
* task_not_completed
* interrupted_task_completed
* interrupted_task_not_completed
"""
DailyReportStatus = Text


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


class Config(DictMixin):
    def __init__(self, timezone, remind_minutes_delta, slack, toggl, todoist,
                 special_events, message_format_by_event, next_message_format,
                 daily_report_format_by_status, special_labels, secret_name, project_by_id):
        self.timezone = timezone  # type: Text
        self.remind_minutes_delta = remind_minutes_delta  # type: int
        self.slack = Slack.from_dict(slack)  # type: Slack
        self.toggl = Toggl.from_dict(toggl)  # type: Toggl
        self.todoist = Todoist.from_dict(todoist)  # type: Todoist
        self.special_events = Event.from_dict2dict(special_events)  # type: Dict[Text, Event]
        self.message_format_by_event = message_format_by_event  # type: Dict[TodoistEvent, Text]
        self.next_message_format = next_message_format  # type: Text
        self.daily_report_format_by_status = daily_report_format_by_status  # type: Dict[DailyReportStatus, Text]
        self.special_labels = SpecialLabels.from_dict(special_labels)  # type: SpecialLabels
        self.secret_name = secret_name  # type: Text
        self.project_by_id = Project.from_dict2dict(project_by_id)  # type: Dict[ProjectId, Project]
