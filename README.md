# Scalyr-Serverless-Demo

This is a sample Servlerless application built using AWS Lambda.  It implements
a very simple image analysis pipeline used to detect spammy images.  This is
meant purely for demo purposes.

## Architecture

The pipeline is made of a total of five Lambdas, listed below.

* analyze_image
* detect_adult_content
* detect_known_bad_content
* detect_spammy_words
* update_spam_score

The first Lambda, `analyze_image` is meant to handle incoming HTTP requests to
begin executing the pipeline for a specific image stored in SE  Its main
responsibility is to enqueue SQS messages to each of the detection Lambdas.

The `detect_adult_content` Lambda determines if the target image contents adult content.
It uses the AWS Rekognition service to actually perform the adult content detection.
Based on the results from Rekognition, it computes a score and enqueues a message
to update the image's overall spam score.

The `detect_known_bad_content` Lambda determines if the target image contents matches
a list of known bad images based on a perceptual hash.  The perceptual hash is implemented
using the `ImageHash` Python library.  Currently, we fake out an actual list of
known bad images.

The `detect_spammy_words` Lambda determines if the target image spam text content
(such as "low mortgage rates!").  It uses the AWS Rekognition service to perform
the OCR and then compares against a list of known spammy words.  Based on this,
it computes a score.  Currently, the list of spammy words is faked.

The `update_spam_score` Lambda is invoked once for each of the detection algorithms
through SQS messages.  It accumulates the individual spam scores and determines
the overall spam score for the image.  The Lambda mimics accessing a database
to retrieve and update the spam score, but this is currently faked for this
implementation.

## Installing

This project is based on the [CDK](https://cdkworkshop.com/).  You will need to install it
and all of its dependencies (which includes NodeJS) to run and
deploy this application.

### Installing NodeJS
First install the CDK. For this you will need NodeJS installed.
To install Node on a Mac:
```
brew install node
```

As well as Python
```
brew install python@3
```


### Installing CDK

Then install the CDK:
```
npm install -g aws-cdk
```

Create a virtualenv:

```
$ python3 -m venv .env
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .env/bin/activate
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

### Configure AWS SDK
To use the CDK, you need the AWS SDK installed, authenticated, and configured.

On Mac you can use:
```
python3 -m pip install awscli
```

Then setup aws to use your AWS account:
```
aws configure
```

### Useful CDK commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation


## Deploying the pipeline

You will first need to follow the [instructions to build the ImageHash Lambda layer](layers)
to build the ImageHash layer in your AWS account and set the appropriate environment
variable.

To deploy the Lambda, execute:

```
cdk deploy spam-detect-pipeline
```

This will deploy all the components for the spam pipeline Lambda application, including an API gateway.
Make a note of the API gateway URL.

You will then want to set up the Scalyr CloudWatch Logs integration to capture
your Lambda's logs.  Please follow the [setup instructions](https://github.com/scalyr/scalyr-aws-serverless/tree/master/cloudwatch_logs).

## Invoking the pipeline

To invoke the pipeline on a particular image, you need to send a `POST` request
to the `/analyze_image` endpoing in the API gateway.  The contents of the
`POST` should be a JSON object similar to this:

```
{
  "ImageURL": "S3://[your-s3-bucket]/my-image.jpg",
  "PostID": "1234567",
  "AccountID": "345463406",
  "SourceDevice": "Android Phone",
  "CreatedTimestamp": "01-15-2020 8:00 AM"
}

```

To view the results, you should examine the logs in Scalyr or CloudWatch.
