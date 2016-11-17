# -*- coding: utf-8 -*-

from typing import List, Optional, Dict
from dictmixin.main import DictMixin

TodoistEvent = str
LabelName = str
ProjectId = str

"""
* task_completed
* task_not_completed
* interrupted_task_completed
* interrupted_task_not_completed
"""
DailyReportStatus = str


class Entity(DictMixin):
    def __init__(self, event, id, project_id,
                 project_name, labels, content, private):
        self.event = event  # type: str
        self.id = id  # type: int
        self.project_id = project_id  # type: int
        self.project_name = project_name  # type: str
        self.labels = labels  # type: List[int]
        self.content = content  # type: str
        self.private = private  # type: bool


class Slack(DictMixin):
    def __init__(self, channel, mention, url, icon_emoji=None, icon_url=None):
        self.channel = channel  # type: str
        self.mention = mention  # type: str
        self.url = url  # type: str
        self.icon_emoji = icon_emoji  # type: Optional[str]
        self.icon_url = icon_url  # type: Optional[str]


class Toggl(DictMixin):
    def __init__(self, api_token, workspace):
        self.api_token = api_token  # type: str
        self.workspace = workspace  # type: int


class Todoist(DictMixin):
    def __init__(self, api_token):
        self.api_token = api_token  # type: str


class Event(DictMixin):
    def __init__(self, id, messages):
        self.id = id  # type: int
        self.messages = messages  # type: List[str]


class Label(DictMixin):
    def __init__(self, id, name):
        self.id = id  # type: int
        self.name = name  # type: str


class Project(DictMixin):
    def __init__(self, name, toggl_id=None):
        self.name = name  # type: str
        self.toggl_id = toggl_id  # type: Optional[int]


class Config(DictMixin):
    def __init__(self, timezone, remind_minutes_delta, slack, toggl, todoist,
                 special_events, message_format_by_event, next_message_format,
                 daily_report_format_by_status, label_by_name, secret_name, project_by_id):
        self.timezone = timezone  # type: str
        self.remind_minutes_delta = remind_minutes_delta  # type: int
        self.slack = Slack.from_dict(slack)  # type: Slack
        self.toggl = Toggl.from_dict(toggl)  # type: Toggl
        self.todoist = Todoist.from_dict(todoist)  # type: Todoist
        self.special_events = Event.from_dict2dict(special_events)  # type: Dict[str, Event]
        self.message_format_by_event = message_format_by_event  # type: Dict[TodoistEvent, str]
        self.next_message_format = next_message_format  # type: str
        self.daily_report_format_by_status = daily_report_format_by_status  # type: Dict[DailyReportStatus, str]
        self.label_by_name = Label.from_dict2dict(label_by_name)  # type: Dict[LabelName, Label]
        self.secret_name = secret_name  # type: str
        self.project_by_id = Project.from_dict2dict(project_by_id)  # type: Dict[ProjectId, Project]
