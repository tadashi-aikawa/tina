# -*- coding: utf-8 -*-

import json
import app

from typing import Text
from datetime import datetime, timedelta
from chalicelib.models import Config

DATE_FORMAT = "%Y/%m/%d %H:%M:%S"  # type: Text


class TestMinus3H:
    def test_normal(self):
        dt = datetime.strptime("2016/11/22 02:20:00", DATE_FORMAT)  # type: datetime
        actual = app.minus3h(dt)  # type: datetime

        assert actual.year == 2016
        assert actual.month == 11
        assert actual.day == 21
        assert actual.hour == 23
        assert actual.minute == 20
        assert actual.second == 0


# -------------------------------

WORK_BEGIN_TASK = 72824136
WORK_END_TASK = 73847457
REPEAT_TASK = 72824144


def item_completed():
    body = {
        "event_name": "item:completed",
        "event_data": {
            "id": REPEAT_TASK,
            "content": u'TINA テスト',
            "labels": [652234],
            "project_id": 156051149,
            "in_history": 0,
            "parent_id": None
        }
    }

    with open('../.tinaconfig') as f:
        config = Config.from_dict(json.load(f))
    app.exec_todoist(config, body)


def item_added():
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


def item_deleted():
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


def reminder_fired():
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
