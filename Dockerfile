# syntax=docker/dockerfile:1

# CREATED: 31-MAR-2022
# LAST EDIT: 31-MAR-2022
# AUTHORS: DUANE
#
# USED TO CREATE STANDARD DOCKER IMAGE WITH ALL PREREQUISITES
# NOTES:
# - DOES NOT USE ALPINE (ref: https://pythonspeed.com/articles/alpine-docker-python/)
# - requirements2.txt GENERATED WITH pipreqs (ref: https://stackoverflow.com/questions/31684375/automatically-create-requirements-txt)

FROM ubuntu:20.04
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y software-properties-common gcc
RUN apt-get update && apt-get install -y python3.8 python3-distutils python3-pip python3-apt git

WORKDIR /app
COPY requirements2.txt requirements.txt

# CLONE/BUILD/INSTALL abakit FROM git
RUN git clone https://github.com/ActiveBrainAtlas2/abakit.git && cd abakit && python -m build && cd ..

#RUN pip install -r requirements.txt


#GIT PULL; BASED ON BRANCH


# SET ENVIRONMENT VARIABLES



#RUN make /app


#CMD python /app/app.py