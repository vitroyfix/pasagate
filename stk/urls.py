from django.urls import path
from stk.views import DashboardSTKPushView, STKCallbackView, TransactionStatusView

urlpatterns = [
    path("push/<int:merchant_id>/", DashboardSTKPushView.as_view(), name="stk-push-dashboard"),
    path("callback/", STKCallbackView.as_view(), name="stk-callback"),
    path("status/<str:checkout_request_id>/", TransactionStatusView.as_view(), name="stk-status"),
]