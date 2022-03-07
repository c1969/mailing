FROM python:3.9.5
COPY requirements.txt /
RUN pip3 install -r /requirements.txt

COPY . /app
WORKDIR /app

CMD ["gunicorn"  , "--bind", "0.0.0.0:8085", "app:app"]