from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.clinic.views import (
    ConsultView,
    HomeCabinetItemViewSet,
    InteractionsView,
    LLMStatusView,
    MedicalCaseViewSet,
    MedicationFeedbackViewSet,
    SymptomCatalogView,
)
from apps.clinic import workflow

router = DefaultRouter()
router.register(r'cabinet', HomeCabinetItemViewSet, basename='cabinet')
router.register(r'feedback', MedicationFeedbackViewSet, basename='feedback')
router.register(r'cases', MedicalCaseViewSet, basename='case')

# 医生 / 患者 / 管理员业务闭环
workflow_router = DefaultRouter()
workflow_router.register(r'departments', workflow.DepartmentViewSet, basename='department')
workflow_router.register(r'schedules', workflow.DoctorScheduleViewSet, basename='doctor-schedule')
workflow_router.register(r'appointments', workflow.AppointmentViewSet, basename='appointment')
workflow_router.register(r'visits', workflow.VisitViewSet, basename='visit')
workflow_router.register(r'exam-orders', workflow.ExamOrderViewSet, basename='exam-order')
workflow_router.register(r'comm-notes', workflow.CommunicationNoteViewSet, basename='comm-note')
workflow_router.register(r'prescriptions', workflow.PrescriptionViewSet, basename='prescription')
workflow_router.register(r'follow-ups', workflow.FollowUpViewSet, basename='follow-up')
workflow_router.register(r'payments', workflow.PaymentViewSet, basename='payment')
workflow_router.register(r'audit-logs', workflow.AuditLogViewSet, basename='audit-log')
workflow_router.register(r'toggles', workflow.FeatureToggleViewSet, basename='toggle')

urlpatterns = [
    path('symptoms/', SymptomCatalogView.as_view(), name='clinic-symptoms'),
    path('consult/', ConsultView.as_view(), name='clinic-consult'),
    path('interactions/', InteractionsView.as_view(), name='clinic-interactions'),
    path('llm-status/', LLMStatusView.as_view(), name='clinic-llm-status'),
    path('workflow/workbench/', workflow.WorkbenchView.as_view(), name='workflow-workbench'),
    path('workflow/backup/', workflow.BackupView.as_view(), name='workflow-backup'),
    path('workflow/doctors/', workflow.DoctorListView.as_view(), name='workflow-doctors'),
    path('workflow/', include(workflow_router.urls)),
    path('', include(router.urls)),
]
