# Docker environment for python3.6
#
# Usage:
#  * build the image:
#    $ docker build -t telemetry .
#  * start the image:
#    $ docker run -it telemetry python telemetry.py

FROM python:3.6-alpine

WORKDIR /usr/src

#RUN pip install cbpro

ADD telemetry.py .

CMD ["/bin/sh"]
