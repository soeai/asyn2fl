import os, sys
from dotenv import load_dotenv
import pause
from apscheduler.schedulers.background import BackgroundScheduler

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))))
sys.path.append(root)


from asynfed.client.algorithms import ClientAsyncFl
from asynfed.client.frameworks.tensorflow import TensorflowFramework
from asynfed.commons.conf import Config

from experiment.cifar_dataset.resnet18 import Resnet18
from experiment.cifar_dataset.data_preprocessing import preprocess_dataset


import json 

load_dotenv()

scheduler = BackgroundScheduler()


with open('conf.json', 'r') as json_file:
    config = json.load(json_file)

prefix = f"{config['client_id']}-record"
# add prefix for local client
current_folder = os.getcwd()
Config.TMP_GLOBAL_MODEL_FOLDER = os.path.join(current_folder, prefix, Config.TMP_GLOBAL_MODEL_FOLDER)
Config.TMP_LOCAL_MODEL_FOLDER = os.path.join(current_folder, prefix, Config.TMP_LOCAL_MODEL_FOLDER)
Config.LOG_PATH = os.path.join(current_folder, prefix, Config.LOG_PATH)



# load queue config
config['queue_consumer']['endpoint'] = os.getenv("queue_consumer_endpoint")
config['queue_producer']['endpoint'] = os.getenv("queue_producer_endpoint")


import tensorflow as tf
print("*" * 20)
if tf.config.list_physical_devices('GPU'):
    tf.config.set_visible_devices(tf.config.list_physical_devices('GPU')[config['gpu_index']], 'GPU')
    print("Using GPU: ", tf.config.list_physical_devices('GPU')[config['gpu_index']])
else:
    print("Using CPU")
print("*" * 20)

# ------------oOo--------------------
# Preprocessing data

data_folder_path = os.path.join(root, "experiment", "data", "cifar_data")

testset_filename = "test_set.pickle"
default_testing_dataset_path = os.path.join(data_folder_path, testset_filename)
test_ds, data_size = preprocess_dataset(default_testing_dataset_path, training = False)


# default_testing_dataset_path = "../../../../data/cifar_data/test_set.pickle"
# test_ds, data_size = preprocess_dataset(default_testing_dataset_path, training = False)
# ------------oOo--------------------

print("-" * 20)
print("-" * 20)
print(f"Begin training proceess with data size of {data_size}")
print("-" * 20)
print("-" * 20)

# Define model
model = Resnet18(input_features= (32, 32, 3), 
                 output_features= 10)


# Define framework
tensorflow_framework = TensorflowFramework(model=model, 
                                           data_size= data_size, 
                                           test_ds= test_ds, 
                                           config=config)


tf_client = ClientAsyncFl(model=tensorflow_framework, config=config)
tf_client.start()
scheduler.start()
pause.days(1) # or it can anything as per your need
