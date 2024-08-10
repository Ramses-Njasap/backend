import json
from rest_framework import serializers
from rest_framework.exceptions import APIException

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# pass request
def errors(field_error: str, for_developer=None, code: str = "BAD_REQUEST",
           status_code: int = 400, main_thread=True, param=None):

    error = {
        "message": {
            "request": code.replace("_", " "),
            "field": field_error,
        },
        "status": {
            "code": code,
            "status_code": status_code
        }
    }

    if for_developer:
        error["developer"] = for_developer

    if main_thread:

        error_raise = serializers.ValidationError(error)
        error_raise.status_code = status_code
        raise error_raise
    
    else:

        channel_layer = get_channel_layer()

        if param and isinstance(param, int):

            async def send_error_data():
                await channel_layer.group_send(
                    f"user_{param}",
                    {
                        'type': 'send.error_data',
                        'error_data': error,
                    }
                )

            # Convert the asynchronous function to a synchronous one
            async_to_sync(send_error_data)()

        else:
            error["message"]["field"] = "SERVER ERROR"
            error["developer"] = f"Websocket URL variable Is {None} Or {type(param)} Whereas `int` Is Needed"
            
            async def send_error_data():
                await channel_layer.group_send(
                    f"user_{param}",
                    {
                        'type': 'send.error_data',
                        'error_data': error,
                    }
                )

            # Convert the asynchronous function to a synchronous one
            async_to_sync(send_error_data)()


def serializer_errors(serializer_errors):
    default_errors = serializer_errors
        
    new_error = []
    
    for field_name, field_errors in default_errors.items():
        error = {
            "message": {
                "request": "BAD REQUEST",
                "field": field_errors[0],
            },
            "status": {
                "code": "BAD_REQUEST",
                "status_code": 400
            },
            "developer": field_errors[0]
        }
        new_error.append(error)

    return new_error


def websocket_errors(g_name: str, info: str, for_developer: str, code: str = "BAD_REQUEST", status_code: int = 400):

    error = {
        "message": {
            "request": code.replace("_", " "),
            "info": info,
        },
        "status": {
            "code": code,
            "status_code": status_code,
        },
        "developer": for_developer,
    }

    async_to_sync(get_channel_layer.group_send)(
        g_name, {
            "type": "Send Notification",
            **error
        }
    )
    
    return


class APIExceptionError(APIException):

    def __init__(self, detail=None, messages=None, status_code=None, code=None):
        if detail is None:
            detail = "An error occurred"
        if messages is None:
            messages = "An error occurred"
        if status_code is None:
            status_code = 400
        if code is None:
            code = "error"
            
        self.messages = messages
        self.status_code = status_code
        self.detail = detail
        self.code = code