# Docker environment for python3.6
#
# Usage:
#  * build the image:
#    $ docker build -t telemetry .
#  * start the image:
#    $ docker run -it telemetry python telemetry.py

FROM python:3.7.0-stretch

ADD requirements.txt .
RUN pip install --user -r requirements.txt

ADD auth_keys.py .
ADD base_level2_order_book.py .
ADD binance_level2_order_book.py .
ADD cbpro_level2_order_book.py .
ADD cbpro_console.py .
ADD global_order_book.py .

CMD ["/bin/sh"]
