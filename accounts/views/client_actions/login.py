# Import necessary libraries and modules from rest_framework
from rest_framework.views import APIView


# Login view class that extends from APIView
class Login:

    def __init__(self, request):
        self.request = request

    # Handle HTTP Post method
    def login(self):
        pass