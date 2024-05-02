#!/bin/bash

sam deploy --template-file sagemaker_train.yaml \
 --stack-name sagemaker-training-job-stack \
 --capabilities CAPABILITY_IAM
