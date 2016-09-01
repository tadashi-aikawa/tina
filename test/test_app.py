# -*- coding: utf-8 -*-

import json
import app


def test():
    body = {
        "event_name": "item:completed",
        "event_data": {
            "id": 75549509,
            "content": u'TINA テスト',
            "project_id": 166337596
        }
    }

    with open('../.tinaconfig') as f:
        config = json.load(f)
    app.exec_todoist(config, body)


def test_reminder_fired():
    body = {
        "event_name": "reminder:fired",
        "event_data": {
            "item_id": 73456319,
            "id": 30228632
        }
    }

    with open('../.tinaconfig') as f:
        config = json.load(f)
    app.exec_todoist(config, body)

test()
test_reminder_fired()