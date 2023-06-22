from asynfed.commons.conf import ClientRoles
from asynfed.commons.messages.message import Message


class ServerInitResponseToClient(Message):
    def __init__(self, client_identifier="", session_id="", client_id=None, model_url=None, global_model_name=None, model_version=None,
                 access_key=None, secret_key=None, bucket_name=None, region_name=None, training_exchange=None,
                 monitor_queue=None, role=ClientRoles.WORKER):
        super().__init__()
        # identification info
        self.client_identifier = client_identifier
        self.session_id = session_id
        self.client_id = client_id
        self.role = role

        # queue config
        self.monitor_queue = monitor_queue
        self.training_exchange = training_exchange

        # storage config
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.region_name = region_name

        # model info
        self.global_model_name = global_model_name
        self.model_url = model_url
        self.model_version = model_version
