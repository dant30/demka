from rest_framework.routers import DefaultRouter

from apps.expenses.views.api import ExpenseCategoryViewSet, ExpenseViewSet


router = DefaultRouter()
router.register("categories", ExpenseCategoryViewSet, basename="expense-category")
router.register("", ExpenseViewSet, basename="expense")

urlpatterns = router.urls