# This project is based on cdkworkshop.com

First install the CDK. For this you will need NodeJS installed.
To install Node on a Mac:
```
brew install node
```

As well as Python3
```
brew install python@3
```

Then install the CDK:
```
npm install -g aws-cdk
```

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization process also creates
a virtualenv within this project, stored under the .env directory.  To create the virtualenv
it assumes that there is a `python3` executable in your path with access to the `venv` package.
If for any reason the automatic creation of the virtualenv fails, you can create the virtualenv
manually once the init process completes.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .env
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .env/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .env\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

You can now begin exploring the source code, contained in the hello directory.
There is also a very trivial test included that can be run like this:

```
$ pytest
```

To add additional dependencies, for example other CDK libraries, just add to
your requirements.txt file and rerun the `pip install -r requirements.txt`
command.

# Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

# Configure AWS SDK
To use the CDK, you need the AWS SDK installed, authenticated, and configured.

On Mac you can use:
```
python3 -m pip install awscli
```

Then setup aws with:
```aws configure
```

# pre-commit hooks for black code formatting

Run this to setup the git hooks:
```
pre-commit install
```

To test it out:
```
pre-commit run --all-files
```

To update pre-commit (i.e. new black version) run:
```
pre-commit autoupdate
```

# What to try:

The stack is defined in hello/hello_stack.py
The Lamabda is defined in lambda/hello.py

You can make a change, then run:
```
cdk diff hello-cdk-1
```

If it looks good, deploy with:
```
cdk deploy hello-cdk-1
```

For the current Lambda test, look for the output in the logs `CdkWorkshopStack.Endpoint` followed by a URL which is the API Gateway that has been automatically attached.

# Scalyr-Serverless-Demo

## S3 Bucket
The bucket `scalyr-serverless-demo` contains sample content
