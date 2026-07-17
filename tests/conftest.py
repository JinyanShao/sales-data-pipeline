import pandas as pd
import pytest


@pytest.fixture
def valid_orders() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "order_id": "O-1",
                "order_date": "2026-01-02",
                "customer_id": "C-1",
                "product_id": "P-1",
                "product_name": " Mouse ",
                "category": "Electronics",
                "quantity": 2,
                "unit_price": 10.0,
                "country": "CH",
                "status": "COMPLETED",
            },
            {
                "order_id": "O-2",
                "order_date": "2026-02-03",
                "customer_id": "C-2",
                "product_id": "P-2",
                "product_name": "Desk",
                "category": "Furniture",
                "quantity": 1,
                "unit_price": 50.0,
                "country": "DE",
                "status": "cancelled",
            },
        ]
    )
