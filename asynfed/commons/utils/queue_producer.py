import pika, uuid
import logging
from time import sleep 

LOGGER = logging.getLogger(__name__)
logging.getLogger('pika').setLevel(logging.WARNING)
LOGGER.setLevel(logging.INFO)

class AmqpProducer(object):
    def __init__(self, configuration: dict, log: bool = False):
        self.conf = configuration
        self.exchange_name = configuration["exchange_name"]
        self.exchange_type = configuration["exchange_type"]
        self.routing_key = configuration["routing_key"]
        self.log_flag = log
        self._setup_connection()

    def _setup_connection(self):
        self.connection = pika.BlockingConnection(pika.URLParameters(self.conf["endpoint"]))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange_name, exchange_type=self.exchange_type)
        self.queue = self.channel.queue_declare(queue=self.conf["queue_name"], exclusive=False)
        self.queue_name = self.queue.method.queue
        self.channel.queue_bind(exchange=self.exchange_name, queue=self.queue_name, routing_key=self.routing_key)


    def send_data(self, body_mess, corr_id=None, routing_key=None, expiration=1000):
        try:
            if corr_id is None:
                corr_id = str(uuid.uuid4())
            if routing_key is None:
                routing_key = self.routing_key
            self.sub_properties = pika.BasicProperties(correlation_id=corr_id, expiration=str(expiration))
            self.channel.basic_publish(exchange=self.exchange_name, routing_key=routing_key,
                                       properties=self.sub_properties, body=body_mess)

        # except pika.exceptions.StreamLostError as e:
        except Exception as e:
            LOGGER.info(e)
            LOGGER.exception("Connection lost. Reconnecting...")
            self._setup_connection()
            # sleep(5)
            self.send_data(body_mess, corr_id, routing_key, expiration)

    def get(self):
        return self.conf