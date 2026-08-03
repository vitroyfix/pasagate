from django.urls import path
from vault.views import MerchantRegisterView, MyMerchantsListView, MerchantDetailView

urlpatterns = [
    path("merchants/register/", MerchantRegisterView.as_view(), name="merchant-register"),
    path("merchants/", MyMerchantsListView.as_view(), name="merchant-list"),
    path("merchants/<int:pk>/", MerchantDetailView.as_view(), name="merchant-detail"),
]