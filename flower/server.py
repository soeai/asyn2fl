import os
import sys
root = os.path.dirname(os.getcwd())
sys.path.append(root)
from datetime import datetime
import flwr as fl
import argparse
from flower.resnet18 import Resnet18
from flower.data_preprocessing import preprocess_dataset
import logging
import numpy as np
import tensorflow as tf

log_folder ="server_logs"
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
weights_folder = "server_weights"

if not os.path.exists(weights_folder):
    os.makedirs(weights_folder)

LOG_FORMAT = '%(levelname) -10s %(asctime)s %(name) -30s %(funcName) -35s %(lineno) -5d: %(message)s'
file_name = f"{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}.log"
file_path = os.path.join("server_log", file_name)

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    filename=file_path,
    filemode='a',
    datefmt='%H:%M:%S'
)

# test_path = 'data/test_set.pickle'
test_path = os.path.join("data", "test_set.pickle")
x_test, y_test, data_size = preprocess_dataset(test_path)

epoch = 200
batch_size = 128
learning_rate = 1e-1
lambda_value = 5e-4

# model
# because we don't need to train on server
# just build a simple model
model = Resnet18(num_classes= 10)


def custom_loss_with_l2_reg(y_true, y_pred):
    l2_loss = tf.add_n([tf.nn.l2_loss(w) for w in model.trainable_weights])
    return tf.keras.losses.categorical_crossentropy(y_true, y_pred) + lambda_value * l2_loss

# Compile the model
model.build(input_shape=(None, 32, 32, 3))
# model.compile("adam", "sparse_categorical_crossentropy", metrics=["accuracy"])
model.compile("adam", loss=custom_loss_with_l2_reg, metrics=["accuracy"])

# #  Check if there's a pretrain weight to load from
# # weight_file = f'server_weights/round-{args.init_round}-weights.npz'
# weight_file = f'server_weights/round-60-weights.npz'
# if os.path.isfile(weight_file):
#     logging.info(f"Loading weights from round 60...")
#     pretrain_weights = np.load(weight_file)
#     model.set_weights([pretrain_weights[key] for key in pretrain_weights.files])


def fit_config(server_round: int):
    """Return training configuration dict for each round."""
    config = {
        "current_round": server_round,
    }
    return config

def get_evaluate_fn(model):
    """Return an evaluation function for server-side evaluation."""
    # The `evaluate` function will be called after every round
    def evaluate(server_round, parameters , config):
        model.set_weights(parameters)  
        loss, accuracy = model.evaluate(x_test, y_test, return_dict=False)
        logging.info(f"Round {server_round} | Loss: {loss} | Accuracy: {accuracy}")
        return loss, {"accuracy": accuracy}
    return evaluate


# def start_server(args):
#     class AggregateCustomMetricStrategy(fl.server.strategy.FedAvg):
#         def aggregate_fit( self, server_round, results, failures):

#             # Call aggregate_fit from base class (FedAvg) to aggregate parameters and metrics
#             aggregated_parameters, aggregated_metrics = super().aggregate_fit(server_round, results, failures)

#             if aggregated_parameters is not None:
#                 # Convert `Parameters` to `List[np.ndarray]`
#                 aggregated_ndarrays: List[np.ndarray] = fl.common.parameters_to_ndarrays(aggregated_parameters)

#                 # Save aggregated_ndarrays
#                 logging.info(f"Saving round {server_round} aggregated_ndarrays...")
#                 np.savez(f"server_weights/round-{server_round}-weights.npz", *aggregated_ndarrays)

#             return aggregated_parameters, aggregated_metrics

#         def aggregate_evaluate(self, server_round, results, failures,):
#             """Aggregate evaluation accuracy using weighted average."""

#             if not results:
#                 return None, {}

#             # Call aggregate_evaluate from base class (FedAvg) to aggregate loss and metrics
#             aggregated_loss, aggregated_metrics = super().aggregate_evaluate(server_round, results, failures)

#             # Weigh accuracy of each client by number of examples used
#             accuracies = [r.metrics["accuracy"] * r.num_examples for _, r in results]
#             examples = [r.num_examples for _, r in results]

#             # Aggregate and print custom metric
#             aggregated_accuracy = sum(accuracies) / sum(examples)
#             logging.info(f"Round {server_round} accuracy aggregated from client results: {aggregated_accuracy}")

#             # Return aggregated loss and metrics (i.e., aggregated accuracy)
#             return aggregated_loss, {"accuracy": aggregated_accuracy}
        
#     strategy = AggregateCustomMetricStrategy(
#         # min_fit_clients=args.min_worker,
#         # min_evaluate_clients=args.min_worker,
#         min_available_clients=args.min_worker,
#         evaluate_fn=get_evaluate_fn(model),
#         on_fit_config_fn=fit_config,
#     )

#     fl.server.start_server(
#         server_address=args.address,
#         config=fl.server.ServerConfig(args.num_rounds),
#         strategy=strategy,
#     )

def start_server(args):
    # The `evaluate` function will be called after every round
    # def evaluate_fn(parameters):
    #     model.set_weights(parameters)  
    #     loss, accuracy = model.evaluate(x_test, y_test, return_dict=False)
    #     logging.info(f"Loss: {loss} | Accuracy: {accuracy}")
    #     return loss, {"accuracy": accuracy}

    class SavingModelStrategy(fl.server.strategy.FedAvg):
        def __init__(self, init_round: int, *args, **kwargs):
            super().__init__(*args, **kwargs)
            
            # Check if there's a pretrain weight to load from
            weights_file_name = f'round-{init_round}-weights.npz'
            weights_file_path = os.path.join(weights_folder, weights_file_name)

            if os.path.isfile(weights_file_path):
                logging.info(f"Loading weights from round {init_round}...")
                pretrain_weights = np.load(weights_file_path)
                model.set_weights([pretrain_weights[key] for key in pretrain_weights.files])

                self.init_round = init_round
            else:
                self.init_round = 0


        def aggregate_fit(self, rnd: int, results, failures):
            aggregated_parameters, aggregated_metrics = super().aggregate_fit(rnd, results, failures)

            if aggregated_parameters is not None:
                aggregated_ndarrays: List[np.ndarray] = fl.common.parameters_to_ndarrays(aggregated_parameters)
                logging.info(f"Saving round {self.init_round + rnd} aggregated_ndarrays...")
                file_name = f"round-{self.init_round + rnd}-weights.npz"
                file_path = os.path.join(weights_folder, file_name)
                np.savez(file_path, *aggregated_ndarrays)

            return aggregated_parameters, aggregated_metrics


    # Create strategy
    strategy = SavingModelStrategy(init_round= args.init_round, 
                                   min_available_clients=args.min_worker, 
                                   initial_parameters=fl.common.ndarrays_to_parameters(model.get_weights()),
                                   evaluate_fn=get_evaluate_fn(model))

    # fl.server.start_server(
    #     server_address=args.address,
    #     config=fl.server.ServerConfig(args.num_rounds),
    #     strategy=strategy,
# )
    fl.server.start_server(
        server_address=args.address,
        config=fl.server.ServerConfig(num_rounds=args.num_rounds),
        strategy=strategy,
        # initial_parameters=fl.common.ndarrays_to_parameters(model.get_weights()),  # set initial parameters for server
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Federated Learning Server")

    parser.add_argument("--address", type=str, default="0.0.0.0:8080", help="Specify the port number")
    parser.add_argument("--min_worker", type=int, default=2, help="Specify the minimum number of workers")
    parser.add_argument("--num_rounds", type=int, default=200, help="Specify the number of iterations")
    parser.add_argument("--init_round", type=int, default=60, help="Specify the initial round to continue training from")


    args = parser.parse_args()
    start_server(args)
