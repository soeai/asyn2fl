import os, sys
root = os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))
sys.path.append(root)

from asynfed.commons.conf import Config
from asynfed.server.server_v2 import Server
from asynfed.server.strategies.AsynFL import AsynFL

from dotenv import load_dotenv
load_dotenv()


conf = {
    "server_id": "test_server_id",
    "t": 30,
    "aws": {
        "access_key": os.getenv("access_key"),
        "secret_key": os.getenv("secret_key"),
        "bucket_name": "run-clientv2-resnet18-5-chunks",
        # "bucket_name": "run-clientv2-resnet18",
        # "bucket_name": "test-logger-clientv2",
        "region_name": "ap-southeast-2",
    },
    "queue_consumer": {
        'exchange_name': 'asynfl_exchange',
        'exchange_type': 'topic',
        'queue_name': 'server_consumer',
        'routing_key': 'server.#',
        'end_point': 'amqps://gocktdwu:jYQBoATqKHRqXaV4O9TahpPcbd8xjcaw@armadillo.rmq.cloudamqp.com/gocktdwu'
    },
    "queue_producer": {
        'exchange_name': 'asynfl_exchange',
        'exchange_type': 'topic',
        'queue_name': 'server_queue',
        'routing_key': 'client.#',
        'end_point': "amqps://gocktdwu:jYQBoATqKHRqXaV4O9TahpPcbd8xjcaw@armadillo.rmq.cloudamqp.com/gocktdwu"
    },
    "influxdb": {
        "url": os.getenv("INFLUXDB_URL"),
        "token": os.getenv("INFLUXDB_TOKEN"),
        "org": os.getenv("INFLUXDB_ORG"),
        "bucket_name": os.getenv("INFLUXDB_BUCKET")
    }
}
strategy = AsynFL()
fedasync_server = Server(strategy, conf, save_log=True)
fedasync_server.start()
