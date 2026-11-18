from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render


@staff_member_required
def expenses_dashboard(request):
    return render(request, "admin/expenses_dashboard.html", {})