# views.py
from django.http import JsonResponse

def sample_view(request):
    return JsonResponse({'message': 'This is a sample view response'}, status=200)
