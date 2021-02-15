from PIL import Image
import face_recognition
from kafka import KafkaConsumer
from json import loads
import pickle
import logging
import time



logging.basicConfig(level=logging.INFO, format='%(message)s')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

time.sleep(30)
logging.info('start face-recognizer')
def image_search(img):
    # Wczytuje obraz
    

    # Znajduje wszystkie twarze, sa zapisane w formacie wspolrzednych (gora,prawo,dol,lewo)
    face_locations = face_recognition.face_locations(image)

    logging.info("I found {} face(s) in this photograph.".format(len(face_locations)))
    logging.info(face_locations)
    
    return face_locations

consumer = KafkaConsumer(
    'topic_test',
    bootstrap_servers=['kafka:9093'],
    auto_offset_reset='earliest',
    enable_auto_commit=True
)

for event in consumer:
    data = event.value
    timestamp, image = pickle.loads(data)
    image_search(image)

