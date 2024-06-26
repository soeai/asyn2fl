import os
import uuid
from typing import List
import re
from abc import ABC, abstractmethod
from time import sleep
import pickle
from typing import Dict
from asynfed.server.objects import Worker
from asynfed.server.storage_connectors.boto3 import ServerStorageBoto3

import math
import sys

import logging
LOGGER = logging.getLogger(__name__)

# from asynfed.server import Server

class CosineLRScheduler:
    def __init__(self, total_update_times: int, initial_learning_rate: float = 0.1, min_learning_rate: float = 0.005):
        self.initial_lr = initial_learning_rate
        self.total_update_times = total_update_times
        self.min_lr = min_learning_rate

    def get_learning_rate(self, current_version: int) -> float:
        if current_version > self.total_update_times:
            return self.min_lr
        lr = 0.5 * self.initial_lr * (1 + math.cos(math.pi * current_version / self.total_update_times))
        return max(lr, self.min_lr)  # Ensure lr doesn't go below 0.001 even during updates within the total update times


class Strategy(ABC):
    """
    This here the Interface of strategy, follow the strategy design pattern.
    Any new strategy will follow this interface. 
    """
    # def __init__(self, server: Server, model_name: str, file_extension: str = "pkl"):
    def __init__(self, server, model_name: str, total_update_times: int = None, 
                file_extension: str = "pkl", initial_learning_rate: float = None):
        
        self._server = server

        self.model_name = model_name
        self.file_extension = file_extension
        self.current_version: int = None
        # change after each update time
        self.global_model_update_data_size = 0
        self.avg_loss = 0.0
        self.avg_qod = 0.0

        # now the lr scheduler is just support consine schedule
        if total_update_times:
            LOGGER.info(f"Synchronous learning rate is turn on. Total update time to create a cosine lr scheduler for {total_update_times} update times")
            self.lr_scheduler = self.get_cosine_lr_scheduler(total_update_times= total_update_times, 
                                                            initial_learning_rate= initial_learning_rate)
            LOGGER.info(f"Initial learning rate value: {self.lr_scheduler.get_learning_rate(0)}")
            LOGGER.info(f"Min learning rate value: {self.lr_scheduler.get_learning_rate(total_update_times)}")
        else:
            self.lr_scheduler = None

    def get_current_global_model_filename(self) -> str:
        # return f"{self.model_name}_v{self.current_version}.pkl"
        # "22.pkl"
        return f"{self.current_version}.{self.file_extension}"
    

    def get_new_global_model_filename(self) -> str:
        # "23.pkl"
        return f"{self.current_version + 1}.{self.file_extension}"


    # strategy also
    # handle the flow of server
    # to get the behavior that they want
    @abstractmethod
    def handle_aggregating_process(self):
        pass

    @abstractmethod
    def handle_client_notify_model(self, message):
        pass


    @abstractmethod
    def select_client(self, all_clients) -> List[str]:
        """ Implement the client selection logic by
        """
        pass

    def get_cosine_lr_scheduler(self, total_update_times: int, initial_learning_rate: float = 0.1):
        lr_scheduler = CosineLRScheduler(total_update_times= total_update_times, initial_learning_rate = initial_learning_rate)
        return lr_scheduler
    
    
    def get_learning_rate(self) -> float:
        current_version = self.current_version or 0
        if self.lr_scheduler is not None:
            lr = self.lr_scheduler.get_learning_rate(current_version - 1)
        else: 
            lr = None
        return lr


    @abstractmethod
    def aggregate(self, completed_workers, cloud_storage, local_storage_path):
        """Aggregate algorithm.
        """
        pass


    def extract_model_version(self, folder_path: str) -> int:
        # Use os.path to split the path into components
        _, filename = os.path.split(folder_path)
        
        # Search for any sequence of digits (\d+) that comes directly before the file extension
        # match = re.search(rf'(\d+){re.escape(self.file_extension)}', filename)
        match = re.search(r'(\d+)\.', filename)  # Look for digits followed by a dot

        # If a match was found, convert it to int and return it
        if match:
            return int(match.group(1))
        
        # If no match was found, return None
        return None

    def _attempt_to_download(self, cloud_storage: ServerStorageBoto3, remote_file_path: str, local_file_path: str) -> bool:
        LOGGER.info("Downloading new client model............")
        attemp = 3

        for i in range(attemp):
            if cloud_storage.download(remote_file_path= remote_file_path, 
                                            local_file_path= local_file_path, try_time= attemp):
                return True
            
            LOGGER.info(f"{i + 1} attempt: download model failed, retry in 5 seconds.")

            i += 1
            if i == attemp:
                LOGGER.info(f"Already try 3 time. Pass this client model: {remote_file_path}")
            sleep(5)

        return False
    

    def _get_model_weights(self, file_path):
        while not os.path.isfile(file_path):
            LOGGER.info("*" * 20)
            LOGGER.info("Sleep 5 second when the the download process is not completed, then retry")
            LOGGER.info(file_path)
            LOGGER.info("*" * 20)
            sleep(5)

        with open(file_path, "rb") as f:
            weights = pickle.load(f)
            
        return weights
    