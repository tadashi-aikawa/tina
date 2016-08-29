# -*- coding: utf-8 -*-

import json
import app


def test():
    body = {
        "event_name": "item:completed",
        "event_data": {
            "id": 74878030,
            "content": u'TINA テスト',
            "project_id": 155075179
        }
    }

    with open('../.tinaconfig') as f:
        config = json.load(f)
    app.exec_todoist(config, body)

test()