FROM python:3.9.7-slim

RUN apt-get update && pip install --upgrade pip
ENV PATH=/sagemaker_app:${PATH}
COPY ./ /sagemaker_app
WORKDIR /sagemaker_app

RUN cd /sagemaker_app && pip install -r requirements.txt
RUN chmod +x /sagemaker_app/train && chmod +x /sagemaker_app/serve
RUN mkdir /opt/ml && mkdir /opt/ml/input
COPY ./config /opt/ml/input/config
