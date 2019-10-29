#!/usr/bin/env python3

from aws_cdk import core

from spam_detection_pipeline.stack import SpamDetectionPipelineStack


app = core.App()
SpamDetectionPipelineStack(app, "spam-detect-pipeline", env={'region': 'us-east-1'})

app.synth()
