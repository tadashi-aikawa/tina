TINA
====

`Todoist/Toggl Intermediate Notification API`

TODO: description

## Requirements

* Python2.7.x
* AWS
    * API Gateway
    * Lambda
    * S3
* Slack
    * Incoming webhook URL
* Todist
    * Webhook URL
* Toggl
    * API token

And you know [chalice](https://github.com/awslabs/chalice).

## Quck start

### Create incoming webhook in slack

See [Setting up and Using Slack Webhooks - YouTube](https://www.youtube.com/watch?v=BcobxHl5wdc)

### Create `.tinaconfig` from `.tinaconfig.sample`.

`message_format_by_event` can use below.

* `content`
* `project_name`

### Upload `.tinaconfig` to AWS S3

upload S3.

### Edit S3 parameters in `app.py`

* REGION
* BUCKET (s3 bucket name)

### Deploying

See [chalice's Quickstart](https://github.com/awslabs/chalice).

### Set Todoist webhook url

Set [Todoist webhook url (Displayed after deploying)](https://developer.todoist.com/#webhooks).

