from asynfed.common.messages import MessageObject

from asynfed.common.config import QueueConfig

import uuid


class DatasetDesc(MessageObject):
    def __init__(self, qod: float = None, chunk_index: int = None, data_size: int = None):
        self.data_size = data_size
        self.qod = qod
        self.chunk_index = chunk_index


class CleaningConfig(MessageObject):
    def __init__(self, clean_storage_period: int = 600, global_keep_version_num: int = 5,
                 local_keep_version_num: int = 5):
        self.clean_storage_period = clean_storage_period
        self.global_keep_version_num = global_keep_version_num
        self.local_keep_version_num = local_keep_version_num 

class LearningRateConfig(MessageObject):
    def __init__(self, fix_lr: bool = True, initial_lr: float = 0.01, 
                min_lr: float = 0.001, decay_steps: int = None):
        # fix lr
        # independent decays lr 
        self.fix_lr = fix_lr
        self.initial_lr = initial_lr
        self.min_lr = min_lr
        self.decay_steps = decay_steps


class TrainingParams(MessageObject):
    def __init__(self, epoch: int = 10000, batch_size: int = 128,
                 regularization: str = "l2", lambda_value: float = 0.0005,
                 learning_rate_config: dict = None, beta: float = 0.6
                 ):
        
        self.epoch = epoch
        self.batch_size = batch_size
        self.regularization = regularization
        self.lambda_value = lambda_value

        learning_rate_config = learning_rate_config or {}
        self.learning_rate_config = LearningRateConfig(**learning_rate_config)

        self.beta = beta

class StopConditions(MessageObject):
    def __init__(self, expected_performance: float = 0.95, expected_loss: float = 0.01):
        self.expected_performance = expected_performance
        self.expected_loss = expected_loss

class TestingParams(MessageObject):
    def __init__(self, gpu_index: int = None, batch_size: int = None):
        self.gpu_index = gpu_index
        self.batch_size = batch_size


class ClientConfig(MessageObject):
    def __init__(self, queue_exchange: str, client_id: str = "", role: str = "trainer", 
                 gpu_index: int = 0, save_log: bool = True, tracking_point: int = None, 
                 download_attempt: int = 10, dataset: dict = None, stop_conditions: dict = None,
                 cleaning_config: dict = None, training_params: dict = None, testing_params: dict = None,
                 queue_consumer: dict = None, queue_producer: dict = None,
                 ):

        # these property provide default values
        self.client_id = client_id or str(uuid.uuid4())

        self.role = role
        self.gpu_index = gpu_index
        self.save_log = save_log
        self.tracking_point = tracking_point

        self.download_attempt = download_attempt

        cleaning_config = cleaning_config or {}
        stop_conditions = stop_conditions or {}
        testing_params = testing_params or {}
        training_params = training_params or {}
        dataset = dataset or {}

        self.cleaning_config = CleaningConfig(**cleaning_config)
        self.stop_conditions = StopConditions(**stop_conditions)
        self.testing_params = TestingParams(**testing_params)

        # these properties need to correctly specify
        self.queue_exchange = queue_exchange
        self.dataset = DatasetDesc(**dataset)
        self.training_params = TrainingParams(**training_params)
        self.queue_consumer = QueueConfig(**queue_consumer)
        self.queue_producer = QueueConfig(**queue_producer)
