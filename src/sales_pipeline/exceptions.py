"""Domain-specific pipeline exceptions."""


class PipelineError(Exception):
    """Base class for expected pipeline failures."""


class IngestionError(PipelineError):
    """Raised when input data cannot be loaded."""


class SchemaValidationError(PipelineError):
    """Raised when input columns do not match the required contract."""
