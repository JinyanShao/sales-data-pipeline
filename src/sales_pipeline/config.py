"""Configuration shared by pipeline stages."""

from dataclasses import dataclass, field
from pathlib import Path

REQUIRED_COLUMNS = (
    "order_id",
    "order_date",
    "customer_id",
    "product_id",
    "product_name",
    "category",
    "quantity",
    "unit_price",
    "country",
    "status",
)

SUPPORTED_STATUSES = frozenset({"pending", "completed", "shipped", "cancelled"})
REVENUE_STATUSES = frozenset({"completed", "shipped"})


@dataclass(frozen=True)
class PipelineConfig:
    """Filesystem and business-rule settings for one pipeline run."""

    input_path: Path = Path("data/raw/sales_orders.csv")
    output_dir: Path = Path("reports")
    run_id: str | None = None
    supported_statuses: frozenset[str] = field(default_factory=lambda: SUPPORTED_STATUSES)
    revenue_statuses: frozenset[str] = field(default_factory=lambda: REVENUE_STATUSES)

    def resolved(self, base_dir: Path | None = None) -> "PipelineConfig":
        """Return a config whose relative paths are anchored at base_dir."""
        base = (base_dir or Path.cwd()).resolve()

        def anchor(path: Path) -> Path:
            return path if path.is_absolute() else base / path

        return PipelineConfig(
            input_path=anchor(self.input_path),
            output_dir=anchor(self.output_dir),
            run_id=self.run_id,
            supported_statuses=self.supported_statuses,
            revenue_statuses=self.revenue_statuses,
        )
