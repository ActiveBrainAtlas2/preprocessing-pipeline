# syntax=docker/dockerfile:1

# CREATED: 31-MAR-2022
# LAST EDIT: 5-APR-2022
# AUTHOR(S): DUANE RINEHART
#
# USED TO CREATE STANDARD DOCKER IMAGE WITH ALL PREREQUISITES
# NOTES:
# - DOES NOT USE ALPINE (ref: https://pythonspeed.com/articles/alpine-docker-python/)
# - requirements2.txt GENERATED WITH pipreqs (ref: https://stackoverflow.com/questions/31684375/automatically-create-requirements-txt)

FROM ubuntu:20.04
FROM aba1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV JAVA_HOME=/bin/java
#ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java
LABEL maintainer="drinehart@ucsd.edu"

# BASE O/S INSTALL AND UPDATES
RUN ls -fs /usr/share/zoneinfo/America/Los_Angeles /etc/localtime
RUN apt install -y --no-install-recommends tzdata
RUN apt update && apt install -y python3.8 python3-distutils python3-pip python3-apt python3.8-venv python-dev
RUN apt install -y software-properties-common gcc libc6-i386 libc6-x32 nano git

# OPENSSH, SUDO, REMOTE ACCESS
RUN apt install -y openssh-server sudo
RUN useradd -rm -d /home/dklab -s /bin/bash -g root -G sudo -u 1000 dklab
RUN echo 'dklab:$pw4UCSD1960!' | chpasswd
RUN service ssh start
EXPOSE 22
CMD ["/usr/sbin/sshd","-D"]

# INSTALL [PYTHON] SYSTEM DEPENDENCIES
RUN pip3 install --upgrade pip
RUN python3 -m pip install build numpy

WORKDIR /app

# CLONE/BUILD/INSTALL abakit FROM git
RUN git clone https://github.com/ActiveBrainAtlas2/abakit.git && cd abakit && python3 -m build
RUN python3 setup.py install
RUN cd ..

# JAVABRIDGE CUSTOM CONFIG (REF: https://stackoverflow.com/questions/51756910/cant-pip-install-javabridge)
# NOTE: python_formats ONLY WORKS WITH ORACLE VERSION OF JAVA DEVELOPMENT KIT
RUN wget https://download.oracle.com/java/18/latest/jdk-18_linux-x64_bin.deb
RUN dpkg -i jdk-18_linux-x64_bin.deb
RUN update-alternatives --install /usr/bin/java java /usr/lib/jvm/jdk-18/bin/java 1
RUN update-alternatives --install /usr/bin/javac javac /usr/lib/jvm/jdk-18/bin/javac 1
RUN JAVA_HOME=/usr/lib/jvm/jdk-18/ pip install javabridge --user
RUN pip3 install python_bioformats

# LATEST VERSION OF THE FOLLOWING:
RUN pip3 install igneous scikit-image vtk tqdm torchtext torch tifffile taskqueue task_queue SQLAlchemy SimpleITK Shapely scipy scikit_image rasterio PyYAML cython numpy

COPY requirements2.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt


#GIT PULL; BASED ON BRANCH


# SET ENVIRONMENT VARIABLES



#RUN make /app


#CMD python /app/app.py