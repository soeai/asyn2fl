from abc import ABC
import logging
import boto3

from asynfed.commons.conf import Config

logging.getLogger(__name__)


class AWSConnector(ABC):
    """Class for connecting to AWS S3"""

    def __init__(self, parent) -> None:

        print(Config.__dict__)
        if "" in [Config.STORAGE_ACCESS_KEY, Config.STORAGE_SECRET_KEY, Config.STORAGE_BUCKET_NAME,
                  Config.STORAGE_REGION_NAME]:
            raise Exception("Storage connector config is not enough, check again.")

        self.parent_thread = parent
        self._s3 = boto3.client('s3', aws_access_key_id=Config.STORAGE_ACCESS_KEY,
                                aws_secret_access_key=Config.STORAGE_SECRET_KEY,
                                region_name=Config.STORAGE_REGION_NAME)
        logging.info(f'Connected to AWS server')

    def upload(self, local_file_path: str, remote_file_path: str, try_time=5):
        """Uploads new global model to AWS"""
        t = 1
        while t < try_time:
            try:
                logging.info(f'Uploading {local_file_path} to {remote_file_path}...')
                self._s3.upload_file(local_file_path, Config.STORAGE_BUCKET_NAME, remote_file_path)
                logging.info(f'Successfully uploaded {local_file_path} to {remote_file_path}')
                self.parent_thread.on_upload(True)
                break
            except Exception as e:
                logging.error(e)
                t += 1
        self.parent_thread.on_upload(False)

    def download(self, remote_file_path, local_file_path, try_time=5):
        """Downloads a file from AWS"""
        t = 1
        while t < try_time:
            try:
                logging.info(f'Saving {remote_file_path} to {local_file_path}...')
                self._s3.download_file(Config.STORAGE_BUCKET_NAME, remote_file_path, local_file_path)
                logging.info(f'Saved {remote_file_path} to {local_file_path}')
                self.parent_thread.on_download(True)
                break
            except Exception as e:
                logging.error(e)
                t += 1
        self.parent_thread.on_download(False)
