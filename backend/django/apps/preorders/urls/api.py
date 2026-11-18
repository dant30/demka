from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.preorders.views.api import (
    CatalogView,
    CategoriesView,
    MyOrdersViewSet,
    PortalLogoutView,
    ProductDetailView,
    RequestOTPView,
    StaffPreorderViewSet,
    VerifyOTPView,
)


portal_auth = [
    path("request-otp/", RequestOTPView.as_view(), name="portal-request-otp"),
    path("verify-otp/", VerifyOTPView.as_view(), name="portal-verify-otp"),
    path("logout/", PortalLogoutView.as_view(), name="portal-logout"),
]

portal_catalog = [
    path("", CatalogView.as_view(), name="portal-catalog"),
    path("categories/", CategoriesView.as_view(), name="portal-categories"),
    path("<int:pk>/", ProductDetailView.as_view(), name="portal-product"),
]

portal_orders = DefaultRouter()
portal_orders.register("", MyOrdersViewSet, basename="portal-order")

staff_router = DefaultRouter()
staff_router.register("", StaffPreorderViewSet, basename="staff-preorder")

urlpatterns = [
    path("portal/auth/", include(portal_auth)),
    path("portal/catalog/", include(portal_catalog)),
    path("portal/orders/", include(portal_orders.urls)),
    path("portal/orders/<int:pk>/cancel/",
         MyOrdersViewSet.as_view({"post": "cancel"}),
         name="portal-order-cancel"),
] + staff_router.urls