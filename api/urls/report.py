from api.views.report import EndDayReportDayWiseAPIView, EndDayReportAPIView, SummaryReport, MasterBillDetailView
from django.urls import path
from api.views.report import BillDetailView

# router.register("customer-product-list", CustomerProductAPI)

urlpatterns = [
    path("enddayreport-list/", EndDayReportAPIView.as_view(), name="enddayreport_list"),
    path("enddayreport-list-daywise/", EndDayReportDayWiseAPIView.as_view(), name="enddayreport_list"),
    path("summary-report/", SummaryReport.as_view(), name="summary-report"),

    path('master-bill-endday/', MasterBillDetailView.as_view(), name='bill-detail'),

    path('bill-endday/', BillDetailView.as_view(), name='bill-detail'),
    # path("product-categories", CategoryAPIView.as_view(), name="product-categories")

] 
 
