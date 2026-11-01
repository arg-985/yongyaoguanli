from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CurrentUserView,
    RegisterView,
    ResetPasswordView,
    SendResetCodeView,
    UserViewSet,
)

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('reset-password/send-code/', SendResetCodeView.as_view(), name='send-reset-code'),
    path('reset-password/confirm/', ResetPasswordView.as_view(), name='reset-password'),
    path('', include(router.urls)),
]
