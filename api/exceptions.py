from rest_framework.exceptions import APIException

class ExternalAPIFailure(APIException):
    status_code = 502
    default_detail = 'External API service temporarily unavailable'