import sys
print('Python %s on %s' % (sys.version, sys.platform))
sys.path.extend(['/Users/tleq/PycharmProjects/AsynFL'])

import os
from fedasync.commons.conf import Config
from fedasync.server.server import Server
from fedasync.server.strategies import Strategy
from fedasync.server.strategies.AsynFL import AsynFL


Config.QUEUE_NAME = "server_queue"
Config.QUEUE_URL = "amqp://guest:guest@localhost:5672/%2F"
Config.TRAINING_EXCHANGE = "training_exchange"


class FedAsyncServer(Server):
    def __init__(self, strategy: Strategy, t=30):
        super().__init__(strategy, t)

    def is_stop_condition(self):
        return False


strategy = AsynFL()
if not os.path.exists(Config.TMP_GLOBAL_MODEL_FOLDER):
    os.makedirs(Config.TMP_GLOBAL_MODEL_FOLDER)
if not os.path.exists(Config.TMP_LOCAL_MODEL_FOLDER):
    os.makedirs(Config.TMP_LOCAL_MODEL_FOLDER)


fedasync_server = FedAsyncServer(strategy)
fedasync_server.server_access_key = 'AKIA2X4RVJV36KLB3BXF'
fedasync_server.server_secret_key = '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'
fedasync_server.run()
