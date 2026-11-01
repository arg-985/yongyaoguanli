from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.family.models import FamilyBinding
from apps.family.serializers import FamilyBindingSerializer

User = get_user_model()


class FamilyBindingViewSet(viewsets.ModelViewSet):
    queryset = FamilyBinding.objects.all()
    serializer_class = FamilyBindingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return FamilyBinding.objects.all()
        if getattr(user, 'role', None) == 'patient':
            return FamilyBinding.objects.filter(patient=user)
        if getattr(user, 'role', None) == 'family':
            return FamilyBinding.objects.filter(family_member=user)
        return FamilyBinding.objects.none()

    def create(self, request, *args, **kwargs):
        user = request.user
        # 只有患者可以添加家属
        if not user.is_staff and getattr(user, 'role', None) != 'patient':
            return Response(
                {'detail': '仅患者可添加家属绑定'},
                status=status.HTTP_403_FORBIDDEN,
            )
        # 前端按用户名提交：{family_username, relation}
        family_username = (request.data.get('family_username') or '').strip()
        relation = request.data.get('relation') or '其他'
        if not family_username:
            return Response(
                {'detail': '请输入家属用户名'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            family_user = User.objects.get(username=family_username)
        except User.DoesNotExist:
            return Response(
                {'detail': f'用户"{family_username}"不存在，请确认家属已注册'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if getattr(family_user, 'role', None) != 'family':
            return Response(
                {'detail': f'用户"{family_username}"不是家属角色，无法绑定'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if family_user.id == user.id:
            return Response(
                {'detail': '不能绑定自己'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        binding, created = FamilyBinding.objects.get_or_create(
            patient=user,
            family_member=family_user,
            defaults={'relation': relation},
        )
        if not created:
            return Response(
                {'detail': '该家属已绑定，请勿重复添加'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(binding)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        binding = self.get_object()
        if user.is_staff:
            return super().destroy(request, *args, **kwargs)
        if getattr(user, 'role', None) == 'patient' and binding.patient_id == user.id:
            return super().destroy(request, *args, **kwargs)
        return Response(
            {'detail': '仅患者本人或管理员可解除绑定'},
            status=status.HTTP_403_FORBIDDEN,
        )
