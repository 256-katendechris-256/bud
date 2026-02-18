import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    """Always return JSON, even for unhandled exceptions."""
    response = exception_handler(exc, context)

    if response is not None:
        return response

    # Unhandled exception — log it and return a JSON 500
    logger.exception("Unhandled API error: %s", exc)
    return Response(
        {"detail": f"Internal server error: {exc}"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
