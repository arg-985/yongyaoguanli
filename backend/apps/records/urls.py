from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.records.views import MedicationRecordViewSet

router = DefaultRouter()
router.register(r'', MedicationRecordViewSet, basename='record')

urlpatterns = [
    path('', include(router.urls)),
]
