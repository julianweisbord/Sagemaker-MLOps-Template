#!/bin/bash

sam deploy --template-file sagemaker_deploy.yaml \
 --stack-name sagemaker-autoscaling-stack \
--capabilities CAPABILITY_IAM
