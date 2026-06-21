"""
Custom Exception Classes for Loan Management System
Provides semantic exception types for better error handling and logging.
"""


class LoanManagementException(Exception):
    """Base exception for all loan management system errors."""

    def __init__(self, message: str, error_code: str = None, context: dict = None):
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.context = context or {}
        super().__init__(self.message)


class LLMCallError(LoanManagementException):
    """Raised when LLM (Claude) invocation fails."""

    def __init__(self, message: str, agent_name: str = None, **context):
        context["agent"] = agent_name
        super().__init__(message, "LLM_CALL_ERROR", context)


class JSONParseError(LoanManagementException):
    """Raised when response JSON parsing fails."""

    def __init__(self, message: str, response_text: str = None, **context):
        if response_text:
            context["response_preview"] = response_text[:200]
        super().__init__(message, "JSON_PARSE_ERROR", context)


class ValidationError(LoanManagementException):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str = None, value: any = None, **context):
        context["field"] = field
        context["value"] = value
        super().__init__(message, "VALIDATION_ERROR", context)


class MCPToolError(LoanManagementException):
    """Raised when MCP tool execution fails."""

    def __init__(self, message: str, tool_name: str = None, **context):
        context["tool"] = tool_name
        super().__init__(message, "MCP_TOOL_ERROR", context)


class TimeoutError(LoanManagementException):
    """Raised when operation exceeds timeout limit."""

    def __init__(self, message: str, timeout_seconds: int = None, **context):
        context["timeout_seconds"] = timeout_seconds
        super().__init__(message, "TIMEOUT_ERROR", context)


class AgentChainError(LoanManagementException):
    """Raised when agent output is invalid or incomplete."""

    def __init__(self, message: str, expected_fields: list = None, **context):
        context["expected_fields"] = expected_fields
        super().__init__(message, "AGENT_CHAIN_ERROR", context)


class DatabaseError(LoanManagementException):
    """Raised when database operations fail."""

    def __init__(self, message: str, operation: str = None, **context):
        context["operation"] = operation
        super().__init__(message, "DATABASE_ERROR", context)
