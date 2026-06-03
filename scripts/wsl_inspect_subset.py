from pathlib import Path
import pickle


def main() -> None:
    root = Path("official/test_subset")
    for path in sorted(root.glob("*.pkl")):
        with path.open("rb") as handle:
            obj = pickle.load(handle)
        print(path.name, type(obj), getattr(obj, "shape", None), flush=True)
        if isinstance(obj, dict):
            print("  keys:", list(obj.keys()), flush=True)
            for key, value in obj.items():
                print(" ", key, type(value), flush=True)
                if isinstance(value, dict):
                    print("    nested keys:", list(value.keys()), flush=True)
                    for nested_key, nested_value in value.items():
                        print(
                            "   ",
                            nested_key,
                            getattr(nested_value, "shape", None),
                            type(nested_value),
                            flush=True,
                        )
                break


if __name__ == "__main__":
    main()
