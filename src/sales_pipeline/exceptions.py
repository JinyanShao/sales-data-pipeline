"""Domain-specific pipeline exceptions."""


class PipelineError(Exception):
    """Base class for expected pipeline failures."""


class InputFileError(PipelineError):
    """Raised when input data cannot be loaded."""


class SchemaValidationError(PipelineError):
    """Raised when input columns do not match the required contract."""


class ExportError(PipelineError):
    """Raised when pipeline artifacts cannot be written."""


class ReconciliationError(PipelineError):
    """Raised when transformed orders and summary totals do not agree."""
