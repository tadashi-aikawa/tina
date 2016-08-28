# -*- coding: utf-8 -*-

from chalice import Chalice
import boto3
import json
import requests

# Set your environmental parameters
REGION = 'ap-northeast-1'
BUCKET = 'mamansoft-tina'
KEY = '.tinaconfig'

S3 = boto3.client('s3', region_name=REGION)
app = Chalice(app_name='tina')
app.debug = True

@app.route('/ping')
def ping():
    return {'result': 'ok'}


def body2entity(body, config):
    project = config['project_by_id'].get(str(body['event_data']['project_id']))
    if not project:
        return None

    return {
        "event": body['event_name'],
        "project_name": project['name'],
        "content": body['event_data']['content']
    }


@app.route('/todoist', methods=['POST'])
def todoist():
    s3_obj = S3.get_object(Bucket=BUCKET, Key=KEY)
    config = json.loads(s3_obj['Body'].read())
    body = app.current_request.json_body
    entity = body2entity(body, config)

    if not entity:
        print('There is no project matched project_id {}'.format(body['event_data']['project_id']))
        return {'result': 'ok'}

    payload = {
        "text": config['message_format_by_event'][entity['event']].format(**entity),
        "username": u"TINA",
        "icon_url": config['slack']['icon_url']
    }

    r = requests.post(config['slack']['url'], data=json.dumps(payload, ensure_ascii=False).encode('utf8'))

    # for debug
    print(r.status_code)
    print(r.content)

    return {'result': 'ok'}
