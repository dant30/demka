from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render


@staff_member_required
def purchasing_dashboard(request):
    return render(request, "admin/purchasing_dashboard.html", {})