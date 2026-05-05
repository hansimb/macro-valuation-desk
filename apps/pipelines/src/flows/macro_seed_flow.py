from prefect import flow

from src.tasks.fetch_seed_data import fetch_seed_data
from src.tasks.load_macro_seed import load_macro_seed


def run_macro_seed_flow() -> dict[str, int]:
    rows = fetch_seed_data.fn()
    return load_macro_seed.fn(rows)


@flow(name="macro-seed-flow")
def macro_seed_flow() -> dict[str, int]:
    return run_macro_seed_flow()

if __name__ == "__main__":
    macro_seed_flow()
