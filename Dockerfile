FROM python:3.12-slim

RUN apt-get clean \
    && apt-get -y update

#RUN apt-get -y install \
#    nginx \
#    python3-dev \
#    build-essential
RUN apt-get -y install git sqlite3

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt --src /usr/local/src
RUN pip install metadatacli/
RUN pip install sqlite3

ENV DB_FP=/app/db.sqlite3
ENV LOG_FP=/app

RUN if [ ! -f ${DB_FP} ]; then; sqlite3 $DB_FP < schema.sql; fi

COPY . .

EXPOSE 5000
CMD [ "python", "app/app.py" ]
