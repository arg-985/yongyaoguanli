from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.family.views import FamilyBindingViewSet

router = DefaultRouter()
router.register(r'bindings', FamilyBindingViewSet, basename='binding')

urlpatterns = [
    path('', include(router.urls)),
]
