from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.medications.views import MedicationViewSet

router = DefaultRouter()
router.register(r'', MedicationViewSet, basename='medication')

urlpatterns = [
    path('', include(router.urls)),
]
