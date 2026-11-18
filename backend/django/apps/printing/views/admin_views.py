from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render


@staff_member_required
def printing_dashboard(request):
    return render(request, "admin/printing_dashboard.html", {})