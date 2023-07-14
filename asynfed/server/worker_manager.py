import logging
from typing import Dict, List

from asynfed.commons.utils.time_ultils import time_diff, time_now
from asynfed.server.objects import Worker

LOGGER = logging.getLogger(__name__)


class WorkerManager:
    def __init__(self) -> None:
        """
            Initialize a WorkerManager object.
            The Worker_pools attribute is a dictionary of Worker objects,keyed by Worker id.
            The history_state attribute is a dictionary that maps epoch numbers
            to dictionaries of Worker objects, keyed by Worker id.
        """

        # all worker information
        self.worker_pool: Dict[str, Worker] = {}

        # save history state by version.
        self.history_state: Dict[int, Dict[str, Worker]] = {}

    def add_worker(self, worker: Worker) -> None:
        """Add a Worker to the worker_pools attribute.
        Args:
            worker (Worker): The Worker object to add.
        """
        # LOGGER.info(f"New worker added, ID: {worker.worker_id}")
        self.worker_pool[worker.worker_id] = worker


    def total(self) -> int:
        """Get the total number of Workers.
        Returns:
            int: The number of Workers in the worker_pools attribute.
        """
        return len(self.worker_pool)

    def get_all_worker(self) -> Dict [str, Worker]:
        """Get all Workers from the worker_pools attribute.
        Returns:
           Dict[str, Worker]: A dictionary of all Worker objects in the
               worker_pools attribute, keyed by Worker id.
        """
        return self.worker_pool

    def add_local_update(self, client_id, message_content: dict):
        # update worker states with information from local worker.
        worker: Worker = self.worker_pool[client_id]
        worker.weight_file = message_content['remote_worker_weight_path']
        worker.current_version = message_content['global_version_used']
        worker.loss = message_content['loss']
        worker.is_completed = True


    # def update_worker_after_training(self):
    #     for worker in self.worker_pool:
    #         self.worker_pool[worker].is_completed = False

    def get_completed_workers(self) -> Dict:
        return {worker_id: self.worker_pool[worker_id] for worker_id in self.worker_pool if self.worker_pool[worker_id].is_completed == True}

    def get_worker_by_id(self, worker_id: str) -> Worker:
        """
        Return a worker object by worker_id
        """
        return self.worker_pool[worker_id]

    def list_sessions(self) -> List:
        """
        Return a list of session_id
        """
        return [self.worker_pool[worker_id].session_id for worker_id in self.worker_pool.keys()]

    def list_connected_workers(self) -> List:
        """
        Return a list of connected worker_id
        """
        return [worker_id for worker_id in self.worker_pool.keys() if self.worker_pool[worker_id].is_connected == True]

    def update_worker_connections(self) -> None:
        """
        Update worker connections
        """
        for worker_id in self.worker_pool.keys():
            if time_diff(time_now(), self.worker_pool[worker_id].last_ping) < 10:
                self.worker_pool[worker_id].is_connected = True
            else:
                self.worker_pool[worker_id].is_connected = False


    def update_worker_last_ping(self, worker_id):
        self.worker_pool[worker_id].last_ping = time_now()

