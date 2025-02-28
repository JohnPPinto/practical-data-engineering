FROM python:3.12

RUN apt-get update

WORKDIR /app

COPY data_loading.py data_loading.py
COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "python", "data_loading.py" ]