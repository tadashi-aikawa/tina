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

And create pipeline job.

### Set build parameters

|     Name    |         Note         |
|-------------|----------------------|
| IMAGE_NAME  | Docker image name    |
| BRANCH_NAME | Checkout branch name |

### Set pipeline

For example.

* Definition: `Pipeline script from SCM`
    * SCM: `Git`
        * Repositories
            * Repository URL: `https://github.com/tadashi-aikawa/tina`
        * Branches to build
            * Branch Specifier (blank for 'any'): `${BRANCH_NAME}`
    * Script Path: Jenkinsfile
