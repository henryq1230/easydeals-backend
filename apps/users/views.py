from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([AllowAny])
def user_list(request):
    """Vista básica para listar usuarios"""
    return Response({
        'message': 'Users API funcionando!',
        'version': '1.0',
        'endpoints': {
            'GET /api/users/': 'Lista de usuarios',
            'POST /api/users/': 'Crear usuario (próximamente)',
        }
    })