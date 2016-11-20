# -*- coding: utf-8 -*-

import json
import app
from chalicelib.models import Config

WORK_BEGIN_TASK = 72824136
WORK_END_TASK = 73847457
REPEAT_TASK = 72824144


def test():
    body = {
        "event_name": "item:completed",
        "event_data": {
            "id": REPEAT_TASK,
            "content": u'TINA テスト',
            "labels": [652234],
            "project_id": 156051149
        }
    }

    with open('../.tinaconfig') as f:
        config = Config.from_dict(json.load(f))
    app.exec_todoist(config, body)


def test_create():
    body = {
        "event_name": "item:added",
        "event_data": {
            "id": 90013592,
            "content": u"てすとのたすく(17:00-18:00)",
            "project_id": 156051149,
            "labels": [652234]
        }
    }

    with open('../.tinaconfig') as f:
        config = Config.from_dict(json.load(f))
    app.exec_todoist(config, body)


def test_delete():
    body = {
        "event_name": "item:deleted",
        "event_data": {
            "id": 90013592,
            "content": u"TINA テスト",
            "project_id": 156051149,
            "labels": [652234]
        }
    }

    with open('../.tinaconfig') as f:
        config = Config.from_dict(json.load(f))
    app.exec_todoist(config, body)


def test_reminder_fired():
    body = {
        "event_name": "reminder:fired",
        "event_data": {
            "item_id": 90013105,
            "id": 33482384
        }
    }

    with open('../.tinaconfig') as f:
        config = Config.from_dict(json.load(f))
    app.exec_todoist(config, body)


test_delete()
