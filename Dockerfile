FROM python:3.13-slim

# Need `git` to install `tablemusthave` as long as it's not on PyPi
RUN apt-get clean && apt-get -y update
RUN apt-get -y --no-install-recommends install curl git vim \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install /app/[web]

ENV METADATA_APP_MODE=full

EXPOSE 80

# This one should be run with gunicorn (probably facing customers)
# but it might take some fiddling to get it to work behind a proxy
CMD [ "gunicorn", "metadatalib.app:app", "--bind", "0.0.0.0:80" ]
