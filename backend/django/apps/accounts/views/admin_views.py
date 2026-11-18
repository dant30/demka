"""Server-rendered admin views for the accounts app (optional)."""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render


@staff_member_required
def accounts_dashboard(request):
    return render(request, "admin/accounts_dashboard.html", {})