from dataclasses import replace

import pytest

from sales_pipeline.cleaning import clean_orders
from sales_pipeline.exceptions import ReconciliationError
from sales_pipeline.reconciliation import reconcile_summaries
from sales_pipeline.transformation import transform_orders
from sales_pipeline.validation import validate_orders


def summaries_for(valid_orders):
    cleaning = clean_orders(valid_orders, validate_orders(valid_orders))
    return transform_orders(cleaning.accepted)


def test_reconcile_summaries_accepts_matching_totals(valid_orders):
    reconcile_summaries(summaries_for(valid_orders))


def test_reconcile_summaries_rejects_revenue_difference(valid_orders):
    summaries = summaries_for(valid_orders)
    customer = summaries.by_customer.copy()
    customer.loc[0, "revenue_cents"] += 1
    inconsistent = replace(summaries, by_customer=customer)
    with pytest.raises(ReconciliationError, match="customer.revenue_cents"):
        reconcile_summaries(inconsistent)


def test_reconcile_summaries_rejects_count_and_unit_differences(valid_orders):
    summaries = summaries_for(valid_orders)
    product = summaries.by_product.copy()
    product.loc[0, "order_count"] += 1
    product.loc[0, "units_ordered"] += 1
    inconsistent = replace(summaries, by_product=product)
    with pytest.raises(ReconciliationError, match="product.order_count") as error:
        reconcile_summaries(inconsistent)
    assert "product.units_ordered" in str(error.value)
