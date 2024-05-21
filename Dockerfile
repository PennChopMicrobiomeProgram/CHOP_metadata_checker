FROM python:3.12-slim

RUN apt-get clean && apt-get -y update
RUN apt-get -y install curl git vim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt
RUN pip install -r dev-requirements.txt
RUN pip install /app/app/metadatalib/

#RUN pytest /app/metadatalib/tests/
#RUN pytest /app/metadatacli/tests/

# Default values, can be overridden by config
ENV DB_HOST=10.30.22.12
ENV DB_USER=postgres
ENV DB_NAME=metadata
ENV URL=metadatachecker.tkg.research.chop.edu

ENTRYPOINT [ "python" ]
CMD [ "app/app.py" ]
