from pathlib import Path
import pickle
import sys

import numpy as np
import tensorflow as tf
from tensorflow.keras.callbacks import Callback
from tensorflow.keras.optimizers import Adam


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_DIR = PROJECT_ROOT / "official" / "AI_model_and_files"
sys.path.insert(0, str(OFFICIAL_DIR))

from utils import BatchGenerator, create_model_lstm, one_hot  # noqa: E402


class EpochLogger(Callback):
    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        print(f"epoch={epoch + 1} logs={logs}", flush=True)


def load_subset(sample_count: int = 2048, validation_count: int = 256):
    subset_dir = PROJECT_ROOT / "official" / "test_subset"
    with (subset_dir / "x1_test_M1_M20_train_val_test_set.pkl").open("rb") as handle:
        x1 = pickle.load(handle)
    with (subset_dir / "x2_test_M1_M20_train_val_test_set.pkl").open("rb") as handle:
        x2_dict = pickle.load(handle)
    with (subset_dir / "y_test_M1_M20_train_val_test_set.pkl").open("rb") as handle:
        y = pickle.load(handle)

    x2 = x2_dict[20][1]
    total = sample_count + validation_count
    return (
        x1[:sample_count],
        x2[:sample_count],
        y[:sample_count],
        x1[sample_count:total],
        x2[sample_count:total],
        y[sample_count:total],
    )


def main() -> None:
    gpus = tf.config.list_physical_devices("GPU")
    print("TensorFlow:", tf.__version__, flush=True)
    print("GPUs:", gpus, flush=True)
    if not gpus:
        raise RuntimeError("TensorFlow did not detect a GPU.")

    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)

    x1_train, x2_train, y_train, x1_val, x2_val, y_val = load_subset()
    y_train_oh = one_hot(y_train)
    y_val_oh = one_hot(y_val)
    print("Training set:", x1_train.shape, x2_train.shape, y_train.shape, flush=True)
    print("Validation set:", x1_val.shape, x2_val.shape, y_val.shape, flush=True)

    strategy = tf.distribute.MirroredStrategy()
    print("Number of synchronized GPUs:", strategy.num_replicas_in_sync, flush=True)
    with strategy.scope():
        model = create_model_lstm(
            input1_shape=x1_train.shape[1:],
            input2_shape=(None, x2_train.shape[-1]),
            output_shape=y_train_oh.shape,
        )
        model.compile(
            optimizer=Adam(learning_rate=0.0001),
            loss="categorical_crossentropy",
            metrics=["categorical_accuracy"],
        )

    train_gen = BatchGenerator(
        [x1_train, x2_train],
        y_train_oh,
        tps=[3, 4, 5, 6, 7, 8, 9, 10, 15, 20],
        error_range=[0, 0.5, 1, 2],
        batch_size=64,
    )
    val_gen = BatchGenerator(
        [x1_val, x2_val],
        y_val_oh,
        tps=[20],
        error_range=[0],
        batch_size=64,
        shuffle=False,
    )

    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=100000,
        callbacks=[EpochLogger()],
    )


if __name__ == "__main__":
    np.random.seed(1)
    main()
