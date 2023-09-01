FROM python:3.10.12-slim

WORKDIR /app
COPY requirements.txt /app/

RUN pip install -r requirements.txt

COPY app.py /app/
COPY config.py /app/
COPY feature_x.py /app/
COPY .env /app/
RUN mkdir voice

CMD ["python", "app.py"]
