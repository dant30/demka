from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render


@staff_member_required
def suppliers_dashboard(request):
    return render(request, "admin/suppliers_dashboard.html", {})