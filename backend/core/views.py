from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.cache import cache
from django.db import connection
import os


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    健康检查端点 - 验证所有服务是否正常运行
    不需要认证即可访问
    """
    status = {
        'status': 'healthy',
        'services': {}
    }

    # 检查数据库连接
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['services']['database'] = 'connected'
    except Exception as e:
        status['services']['database'] = f'error: {str(e)}'
        status['status'] = 'unhealthy'

    # 检查 Redis 连接
    try:
        cache.set('health_check', 'ok', 10)
        result = cache.get('health_check')
        if result == 'ok':
            status['services']['redis'] = 'connected'
        else:
            status['services']['redis'] = 'error: cache verification failed'
            status['status'] = 'unhealthy'
    except Exception as e:
        status['services']['redis'] = f'error: {str(e)}'
        status['status'] = 'unhealthy'

    # 返回环境信息
    status['environment'] = {
        'debug': os.getenv('DEBUG', 'False'),
        'django_version': __import__('django').get_version(),
    }

    # 根据健康状态返回不同的 HTTP 状态码
    http_status = 200 if status['status'] == 'healthy' else 503

    return Response(status, status=http_status)