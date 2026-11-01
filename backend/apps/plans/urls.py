from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.plans.views import MedicationPlanViewSet, PlanReminderViewSet

router = DefaultRouter()
router.register(r'plans', MedicationPlanViewSet, basename='plan')
router.register(r'reminders', PlanReminderViewSet, basename='reminder')

urlpatterns = [
    path('', include(router.urls)),
]
