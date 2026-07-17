"""Input loading for sales order data."""

from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError, ParserError

from sales_pipeline.exceptions import IngestionError


def read_orders(path: Path) -> pd.DataFrame:
    """Read a CSV file while preserving business identifiers as strings."""
    path = Path(path)
    if not path.exists():
        raise IngestionError(f"Input file does not exist: {path}")
    if not path.is_file():
        raise IngestionError(f"Input path is not a file: {path}")

    try:
        return pd.read_csv(
            path,
            dtype={
                "order_id": "string",
                "customer_id": "string",
                "product_id": "string",
            },
            keep_default_na=True,
        )
    except EmptyDataError as exc:
        raise IngestionError(f"Input file is empty: {path}") from exc
    except (ParserError, UnicodeDecodeError, OSError) as exc:
        raise IngestionError(f"Could not read input file {path}: {exc}") from exc
