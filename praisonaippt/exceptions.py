"""Typed exceptions for praisonaippt.

These exist so programmatic callers can distinguish between failure modes
without parsing strings. Existing callers that expect ``None`` returns from
``loader.load_verses_from_file`` are unaffected — those swallow exceptions
internally.
"""


class PraisonAIPPTError(Exception):
    """Base class for all praisonaippt-specific errors."""


class LoaderError(PraisonAIPPTError):
    """Raised when a verses file cannot be opened or parsed."""


class SchemaError(LoaderError):
    """Raised when verses data does not match the expected schema."""


class BackendUnavailableError(PraisonAIPPTError):
    """Raised when no PDF backend (Aspose / LibreOffice) is available."""
