TINA
====

[![Build Status](http://mamansoft.net:8888/job/TINA-Production-Deploy/badge/icon)](http://mamansoft.net:8888/job/TINA-Production-Deploy/)

`Todoist/Toggl Intermediate Notification API`

TINA can Notify slack of following things about in a few seconds.   

* Your todoist events (create, complete, delete, remind)
* Your next task (when you completes task)
* Special behavior (work-start, work-end, lunch... etc)
 
TODO: Write more information


## Requirements

* Python2.7.x
* AWS
    * API Gateway
    * Lambda
    * S3
* Slack
    * [Incoming webhook URL](https://api.slack.com/incoming-webhooks)  
* Todist (premium)
    * [Webhook URL](https://developer.todoist.com/index.html)
* Toggl
    * [API token](https://github.com/toggl/toggl_api_docs)

And you know [chalice](https://github.com/awslabs/chalice).

## Quck start

### Create incoming webhook in slack

See [Setting up and Using Slack Webhooks - YouTube](https://www.youtube.com/watch?v=BcobxHl5wdc)

### Create `.tinaconfig` from `.tinaconfig.sample`.

`message_format_by_event`, `next_message_format` can use below.

* `content`
* `project_name`

`daily_report_format_by_status` can use below.

* `elapsed`
* `task`
* `project_name`

### Upload `.tinaconfig` to AWS S3

For example

```
$ aws s3 cp .tinaconfig s3://mamansoft-tina/
```

### Edit S3 parameters in `app.py`

* REGION
* BUCKET (s3 bucket name)

### Deploying

See [chalice's Quickstart](https://github.com/awslabs/chalice).

### Set Todoist webhook url

Set [Todoist webhook url (Displayed after deploying)](https://developer.todoist.com/#webhooks).


## CI with Jenkins and Docker

You must set below environmental values.

|          Name         | Environmental value | Credential |
|-----------------------|---------------------|------------|
| AWS_ACCESS_KEY_ID     | x (must be secure!) | o          |
| AWS_SECRET_ACCESS_KEY | x (must be secure!) | o          |
| AWS_DEFAULT_REGION    | o                   |            |

And build parameters.

|     Name    |         Note         |
|-------------|----------------------|
| IMAGE_NAME  | Docker image name    |

Then create pipeline job.

### Build Triggers

Chcek `Build when a change is pushed to Github`.

### Pipeline

* Definition: `Pipeline script from SCM`
    * SCM: `Git`
        * Repositories
            * Repository URL: `https://github.com/tadashi-aikawa/tina`
        * Branches to build
            * Branch Specifier (blank for 'any'): `*/master`
    * Script Path: `Jenkinsfile`
