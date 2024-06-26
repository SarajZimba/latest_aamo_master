from django.urls import path
from api.views.organization import OrganizationApi, BranchApi, PrinterSettingListView
from rest_framework import routers

router = routers.DefaultRouter()

router.register("organization", OrganizationApi)
router.register("branch", BranchApi)

urlpatterns = [
    path('printer-setting/<int:branch_id>/<int:terminal_no>', PrinterSettingListView.as_view(), name='printer-setting'),
    ] + router.urls
