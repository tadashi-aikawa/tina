# -*- coding: utf-8 -*-

from __future__ import unicode_literals

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

DEVELOPMENT_PROJECT = 166337596
FUSHIME_PROJECT = 156051149


def item_completed():
    body = {
        "event_name": "item:completed",
        "event_data": {
            "id": 95746613,
            "content": 'TINA テスト',
            "labels": [652234],
            "project_id": DEVELOPMENT_PROJECT,
            "in_history": 0,
            "parent_id": None,
            "is_deleted": 0,
            "due_date": "Tue 08 Nov 2016 14:59:59 +0000",
            "is_archived": 0,
            "priority": 1,
            "indent": 1,
            "checked": 1,
            "assigned_by_uid": 5612524,
            "date_added": "Sun 23 Oct 2016 09:39:51 +0000",
            "user_id": 5612524,
            "due_date_utc": "Tue 08 Nov 2016 14:59:59 +0000",
            "sync_id": None,
            "responsible_uid": None,
            "item_order": 521,
            "date_string": "11月 8日",
            "date_lang": "ja",
            "collapsed": 0
        }
    }

    with open('../.tinaconfig') as f:
        config = Config.from_yaml(f)
    app.exec_todoist(config, body)


def item_added():
    body = {
        "event_name": "item:added",
        "event_data": {
            "id": 39764256,
            "content": "てすとのたすく",
            "project_id": DEVELOPMENT_PROJECT,
            "labels": [652233],
            "in_history": 0,
            "parent_id": None,
            "is_deleted": 0,
            "due_date": "Wed 16 Nov 2016 14:59:59 +0000",
            "is_archived": 0,
            "priority": 1,
            "indent": 1,
            "checked": 1,
            "assigned_by_uid": None,
            "date_added": "Tue 08 Nov 2016 00:33:32 +0000",
            "user_id": 5612524,
            "due_date_utc": "Wed 16 Nov 2016 14:59:59 +0000",
            "sync_id": None,
            "responsible_uid": None,
            "item_order": 523,
            "date_string": "11月 16日",
            "date_lang": "ja",
            "collapsed": 0
        }
    }

    with open('../.tinaconfig') as f:
        config = Config.from_yaml(f)
    app.exec_todoist(config, body)


def item_deleted():
    body = {
        "event_name": "item:deleted",
        "event_data": {
            "id": 90013592,
            "content": "TINA テスト",
            "project_id": DEVELOPMENT_PROJECT,
            "labels": [652234],
            "in_history": 0,
            "parent_id": None,
            "is_deleted": 0,
            "due_date": "Wed 16 Nov 2016 14:59:59 +0000",
            "is_archived": 0,
            "priority": 1,
            "indent": 1,
            "checked": 1,
            "assigned_by_uid": None,
            "date_added": "Tue 08 Nov 2016 00:33:32 +0000",
            "user_id": 5612524,
            "due_date_utc": "Wed 16 Nov 2016 14:59:59 +0000",
            "sync_id": None,
            "responsible_uid": None,
            "item_order": 523,
            "date_string": "11月 16日",
            "date_lang": "ja",
            "collapsed": 0
        }
    }

    with open('../.tinaconfig') as f:
        config = Config.from_yaml(f)
    app.exec_todoist(config, body)


def reminder_fired():
    body = {
        "event_name": "reminder:fired",
        "event_data": {
            "item_id": 95746613,
            "id": 33482384
        }
    }

    with open('../.tinaconfig') as f:
        config = Config.from_yaml(f)
    app.exec_todoist(config, body)

#item_added()
