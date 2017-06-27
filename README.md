TINA
====

`Todoist/Toggl Intermediate Notification API`

----

Deploy status [![Build Status](https://jenkins.mamansoft.net/job/TINA-Production-Deploy/badge/icon)](https://jenkins.mamansoft.net/job/TINA-Production-Deploy/)

[![Test Status](https://travis-ci.org/tadashi-aikawa/tina.svg?branch=master)](https://travis-ci.org/tadashi-aikawa/tina.svg?branch=master)
[![Test Coverage](https://codeclimate.com/github/tadashi-aikawa/tina/badges/coverage.svg)](https://codeclimate.com/github/tadashi-aikawa/tina/coverage)
[![Code Climate](https://codeclimate.com/github/tadashi-aikawa/tina/badges/gpa.svg)](https://codeclimate.com/github/tadashi-aikawa/tina)
[![](https://img.shields.io/github/license/mashape/apistatus.svg)]()
[![](https://img.shields.io/badge/python-2.7-blue.svg)]()

----

TINA can Notify slack of following things about in a few seconds.

* Your todoist events (create, complete, delete, remind)
* Your next task (when you completes task)
* Special behavior (work-start, work-end, lunch... etc)

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

And you should use [chalice](https://github.com/awslabs/chalice).

## Quck start

### Create incoming webhook in slack

See [Setting up and Using Slack Webhooks - YouTube](https://www.youtube.com/watch?v=BcobxHl5wdc)

### Create `.tinaconfig` from `.tinaconfig.sample`.

You can use following variables in `message_format_by_event`, `next_message_format`, `remind.message_format` ...

|   name       |      type     |
|--------------|---------------|
| event        | Text          |
| project_name | Text          |
| labels       | List[int]     |
| content      | Text          |

in `daily_report_format.base` ...

|   name             | type |
|--------------------|------|
| name               | Text |
| project_name       | Text |
| elapsed [minutes] | int  |
| estimate [minutes]| int  |
| lag [minutes]     | Text |

in `morning_report_format.base` ...

|   name             | type |
|--------------------|------|
| name               | Text |
| project_name       | Text |
| estimate_label     | Text |


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
