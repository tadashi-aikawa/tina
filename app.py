# -*- coding: utf-8 -*-

import json

import boto3
import requests
from pydash import py_
from chalice import Chalice

# Set your environmental parameters
REGION = 'ap-northeast-1'
BUCKET = 'mamansoft-tina'
KEY = '.tinaconfig'

TOGGL_API_URL = 'https://www.toggl.com/api/v8'
TODOIST_API_URL = 'https://todoist.com/API/v7'

S3 = boto3.client('s3', region_name=REGION)
app = Chalice(app_name='tina')
app.debug = True


@app.route('/ping')
def ping():
    return {'result': 'ok'}


def notify_slack(message, config):
    payload = {
        "text": message,
        "username": u"TINA",
        "icon_emoji": config['slack']['icon_emoji'],
        "icon_url": config['slack']['icon_url'],
        "link_names": 1
    }
    r = requests.post(config['slack']['url'], data=json.dumps(payload, ensure_ascii=False).encode('utf8'))
    # for debug
    print(r.status_code)
    print(r.content)

    return r


def exec_remind(body, config):
    entity = {
        "id": str(body['event_data']['item_id'])
    }
    r = requests.post(TODOIST_API_URL + '/sync', data={
        "token": config['todoist']['api_token'],
        "sync_token": "*",
        "resource_types": '["items"]'
    })
    item = py_.find(r.json()['items'], lambda x: str(x['id']) == entity['id'])
    r = notify_slack(
        u"@{}\n もうすぐ *{}* の時間だよ".format(config['slack']['mention'], item['content']),
        config
    )

def exec_todoist(config, body):
    if body['event_name'] == 'reminder:fired':
        exec_remind(body, config)
        return True
    else:
        project_id = str(body['event_data']['project_id'])
        project = config['project_by_id'].get(project_id)
        entity =  {
            "event": body['event_name'],
            "id": str(body['event_data']['id']),
            "project_id": project_id,
            "project_name": project and project.get('name'),
            "content": body['event_data']['content']
        }

        if not entity['project_name']:
            print('There is no project matched project_id {}'.format(entity['project_id']))
            return True

        special_message = config['message_format_by_id'].get(entity['id'])
        r = notify_slack(special_message or config['message_format_by_event'][entity['event']].format(**entity),
                         config)

        # Toggl action (only if needed)
        def accessToggl(path):
            return requests.get(TOGGL_API_URL + path, auth=(config['toggl']['api_token'], 'api_token'))

        if entity['event'] != 'item:completed':
            return True
        current_entry = accessToggl('/time_entries/current').json()['data']
        if not current_entry or current_entry['description'] != entity['content']:
            return True

        accessToggl('/time_entries/{}/stop'.format(current_entry['id']))

        return True


@app.route('/todoist', methods=['POST'])
def todoist():
    s3_obj = S3.get_object(Bucket=BUCKET, Key=KEY)
    config = json.loads(s3_obj['Body'].read())
    body = app.current_request.json_body

    return {'is_success': exec_todoist(config, body)}
