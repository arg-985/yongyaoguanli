from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsRole
from .serializers import UserRegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class CurrentUserView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


def _audit(request, action, target='', detail=''):
    """写入系统审计日志（失败不影响主流程）。"""
    try:
        from apps.clinic.models import AuditLog
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            username=getattr(request.user, 'username', '') or '',
            role=getattr(request.user, 'role', '') or '',
            action=action,
            target=target,
            detail=detail,
            ip=(request.META.get('REMOTE_ADDR') or '')[:64],
        )
    except Exception:
        pass


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsRole('admin')]

    def get_queryset(self):
        qs = super().get_queryset().order_by('id')
        role = self.request.query_params.get('role')
        if role:
            qs = qs.filter(role=role)
        return qs

    def perform_create(self, serializer):
        user = serializer.save()
        _audit(self.request, 'create_account', f'用户 {user.username}', f'角色：{user.get_role_display()}')

    def perform_update(self, serializer):
        user = serializer.save()
        _audit(self.request, 'update_account', f'用户 {user.username}', f'角色：{user.get_role_display()}，启用：{user.is_active}')

    def perform_destroy(self, instance):
        _audit(self.request, 'delete_account', f'用户 {instance.username}', '注销账号')
        instance.delete()

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        """管理员重置密码，返回临时密码。"""
        import random
        user = self.get_object()
        temp = 'tmp' + ''.join(random.choice('abcdefghijkmnpqrstuvwxyz23456789') for _ in range(6))
        user.set_password(temp)
        user.save()
        _audit(request, 'reset_password', f'用户 {user.username}', f'临时密码：{temp}')
        return Response({'temp_password': temp})


# ---------------- 忘记密码（手机号找回） ----------------
# 开发模式：验证码直接返回给前端（不真发短信）
# 生产环境替换为接入 SMS 服务后仅返回 ok

_reset_store = {}  # phone -> { code, expires_at, attempts }


class SendResetCodeView(APIView):
    """根据手机号生成 6 位验证码，返回给前端"""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        phone = (request.data.get('phone') or '').strip()
        if not phone:
            return Response({'detail': '请输入手机号'}, status=status.HTTP_400_BAD_REQUEST)
        import re
        if not re.match(r'^1\d{10}$', phone):
            return Response({'detail': '手机号格式不正确'}, status=status.HTTP_400_BAD_REQUEST)
        if not User.objects.filter(phone=phone).exists():
            # 安全：不泄露手机号是否存在，统一返回 ok
            _reset_store[phone] = {'code': '000000'}
            return Response({'ok': True, 'dev_code': '000000'})
        import random, time
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        _reset_store[phone] = {'code': code, 'expires_at': time.time() + 600, 'attempts': 0}
        return Response({'ok': True, 'dev_code': code})


class ResetPasswordView(APIView):
    """用手机号 + 验证码重置密码"""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        phone = (request.data.get('phone') or '').strip()
        code = (request.data.get('code') or '').strip()
        new_password = request.data.get('new_password') or ''

        if not phone or not code or not new_password:
            return Response({'detail': '请完整填写手机号、验证码和新密码'}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_password) < 6:
            return Response({'detail': '新密码至少 6 位'}, status=status.HTTP_400_BAD_REQUEST)

        import time
        entry = _reset_store.get(phone)
        # 开发环境兜底：没有就当作"000000"
        expected = entry.get('code') if entry else '000000'
        if entry and entry.get('expires_at') and time.time() > entry['expires_at']:
            return Response({'detail': '验证码已过期，请重新获取'}, status=status.HTTP_400_BAD_REQUEST)
        if code != expected:
            return Response({'detail': '验证码错误'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({'detail': '未找到该手机号注册的账号'}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.save()
        _reset_store.pop(phone, None)
        return Response({'ok': True})
