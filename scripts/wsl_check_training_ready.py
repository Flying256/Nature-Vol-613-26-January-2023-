from pathlib import Path
import pickle

import tensorflow as tf


def main() -> None:
    print("TensorFlow:", tf.__version__)
    print("GPUs:", tf.config.list_physical_devices("GPU"))

    root = Path("Data")
    for name in [
        "x1_train_M1_M20_train_val_test_set.pkl",
        "x2_train_M1_M20_train_val_test_set.pkl",
        "y_train_M1_M20_train_val_test_set.pkl",
    ]:
        with (root / name).open("rb") as handle:
            obj = pickle.load(handle)
        print(name, getattr(obj, "shape", None), type(obj))


if __name__ == "__main__":
    main()
