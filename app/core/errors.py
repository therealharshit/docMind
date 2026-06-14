from enum import StrEnum


class ErrorCode(StrEnum):
    UNSUPPORTED_FILE_TYPE = "unsupported_file_type"
    FILE_TOO_LARGE = "file_too_large"
    EMPTY_FILE = "empty_file"
    PARSER_FAILED = "parser_failed"
    ENCRYPTED_PDF = "encrypted_pdf"
    CORRUPT_DOCUMENT = "corrupt_document"
    OLLAMA_UNAVAILABLE = "ollama_unavailable"
    OLLAMA_TIMEOUT = "ollama_timeout"
    LLM_JSON_INVALID = "llm_json_invalid"
    GOOGLE_API_ERROR = "google_api_error"
    GOOGLE_TIMEOUT = "google_timeout"
    LLM_PROVIDER_INVALID = "llm_provider_invalid"
    JOB_NOT_FOUND = "job_not_found"
    RESULT_NOT_READY = "result_not_ready"
    INTERNAL_ERROR = "internal_error"


class AppError(Exception):
    """Base exception for expected domain failures."""

    def __init__(self, code: ErrorCode, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


class UnsupportedFileTypeError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(ErrorCode.UNSUPPORTED_FILE_TYPE, message, retryable=False)


class ParserError(AppError):
    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(code, message, retryable=False)


class LLMError(AppError):
    def __init__(self, code: ErrorCode, message: str, retryable: bool = True) -> None:
        super().__init__(code, message, retryable=retryable)
