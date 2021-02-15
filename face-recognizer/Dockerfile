FROM jjanzic/docker-python3-opencv:opencv-4.0.1

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./app/forP.py .

CMD [ "python", "./forP.py" ]