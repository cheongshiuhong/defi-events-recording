# pull official base image
FROM python:3.9.13-slim-buster

# set work directory
WORKDIR /usr

# setup gcc for cython support
# RUN apt-get update
# RUN apt-get install -y gcc

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt

# copy the source files
COPY src src
