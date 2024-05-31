FROM python:3.12-slim

# Need `git` to install `tablemusthave` as long as it's not on PyPi
RUN apt-get clean && apt-get -y update
RUN apt-get -y --no-install-recommends install curl git vim \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt
RUN pip install -r dev-requirements.txt
RUN pip install /app/app/metadatalib/

ENTRYPOINT [ "python" ]
CMD [ "app/app.py" ]
