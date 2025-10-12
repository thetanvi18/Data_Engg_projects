from time import sleep
from json import dumps
from kafka import KafkaProducer
import random
import time

topic_name='car_speed'

def custom_partitioner(key, all_partitions, available):
    print(f"The key is: {key.decode('UTF-8')}")
    print(f"All partitions: {all_partitions}")
    return int(key.decode('UTF-8')) % len(all_partitions)

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda x: dumps(x).encode('utf-8'),
    partitioner=custom_partitioner
)

car_list = ["Honda", "Ford", "Tesla", "Volvo"]
car_speed = [10, 20, 40, 100, 90, 65]

for e in range(1000):
    data = {
        "car_id": e,
        "car_name": random.choice(car_list),
        "car_speed": random.choice(car_speed),
        "capture_time": int(time.time())
    }
    print("Inserting the data: ", data)
    producer.send(topic_name, key=str(e).encode(), value=data)
    sleep(1)