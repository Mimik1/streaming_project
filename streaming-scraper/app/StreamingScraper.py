__author__ = "Adam Klekowski"

import yaml
import time
from kafka import KafkaProducer
import cv2
import pickle
import logging
import pafy
import pymongo
import numpy as np
import sys
import threading

logging.basicConfig(level=logging.INFO, format='%(message)s')

def cam_init(_url):
    try:
        if 'youtu' in _url:
            vPafy = pafy.new(_url)
            print('ok1')
            play = vPafy.getbest(preftype='mp4')
            print('ok2')
            vidcap = cv2.VideoCapture(play.url)
            print('ok3')
        else:
            vidcap = cv2.VideoCapture(_url)
    except Exception as e:
        logging.error(f"Problem occured during establishing connection to camera\n{e.args}")
        return None
    
    return vidcap


#time.sleep(30)
class StreamingScraper(object):
    def __init__(self):
        with open("scraper_config.yaml") as yaml_file:
            config_dict = yaml.load(yaml_file)["config_dictionary"]

        self.db = pymongo.MongoClient(
                    'mongo1:27017',
                    username=config_dict['mongo_user'],
                    password=config_dict['mongo_password'],
                    authSource=config_dict['mongo_database'],
                    authMechanism='SCRAM-SHA-256')[config_dict['mongo_database']]
        try:
            self.db.list_collections()
        except Exception as e:
            logging.error(f"Problem with connection to MongoDB\n{e.args}")
            sys.exit(2)
        self.collection = self.db[config_dict['collection']]
        self.sample_period = 1/config_dict['sample_freq_Hz']
        self.producer = KafkaProducer(bootstrap_servers=['kafka:9093'])  
    

    def start(self,_url,lock,threads):
        capture_time = time.time()
        while _url in threads:
            if capture_time<time.time():
                timestamp = round(time.time(),2)
                vidcap = cam_init(_url)
                if vidcap is None:
                    logging.error(f"can not establish connection {_url}")
                    continue
                success,image = vidcap.read()
                if success:
                    image = cv2.resize(image, (1280,720))
                    id = str(int(timestamp))+f'_{np.random.randint(999):0=3d}'
                    msg = pickle.dumps((id,timestamp,_url))
                    with lock:
                        self.collection.insert({'id':id,'timestamp':timestamp,'photo':pickle.dumps(image)})
                        self.producer.send('topictest', msg)
                    logging.info(f'Frame captured and sent {id} from {_url}')
                capture_time=self.sample_period+time.time()
            time.sleep(0.5)
    
    def start_manager(self):
        lock = threading.Lock()
        settings = self.db["app_settings"]
        threads = {}
        while True:
            links = [*settings.find()]
            urls = [i["url"] for i in links]
            for i in threads:
                if i not in urls:
                    temp = threads[i]
                    del(threads[i])
                    temp.join()
            
            for i in urls:
                if i not in threads:
                    threads[i] = threading.Thread(target=self.start,args=(i,lock,threads))
                    threads[i].start()
            time.sleep(10)




        



if __name__ == "__main__":
    streaming_scraper = StreamingScraper()
    streaming_scraper.start_manager()