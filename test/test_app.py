# -*- coding: utf-8 -*-

import json
import app

WORK_BEGIN_TASK = 72824136
WORK_END_TASK = 73847457
REPEAT_TASK = 72824144


def test():
    body = {
        "event_name": "item:completed",
        "event_data": {
            "id": WORK_END_TASK,
            "content": u'TINA テスト',
            "labels": [652234],
            "project_id": 156051149
        }
    }

    with open('../.tinaconfig') as f:
        config = json.load(f)
    app.exec_todoist(config, body)


def test_reminder_fired():
    body = {
        "event_name": "reminder:fired",
        "event_data": {
            "item_id": 85474444,
            "id": 33482384
        }
    }

    with open('../.tinaconfig') as f:
        config = json.load(f)
    app.exec_todoist(config, body)


test()
