import os
import django
import json

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.test import RequestFactory
from accounts.models import User
from modules.reports.views import admin_dashboard_page

u = User.objects.filter(is_superuser=True).first()
rf = RequestFactory()

for g in ["daily", "weekly", "monthly"]:
    req = rf.get(f"/admin-dashboard/?grouping={g}")
    req.user = u
    resp = admin_dashboard_page(req)
    content = resp.content.decode("utf-8")
    
    # Check script tag
    start = content.find('id="revenueChartData"')
    end = content.find('</script>', start)
    json_str = content[start+len('id="revenueChartData" type="application/json">'):end].strip()
    data = json.loads(json_str)
    print(f"--- {g.upper()} HTML ---")
    print("Labels:", data.get("labels")[:4], "...", data.get("labels")[-1:])
    print("Count:", len(data.get("labels", [])))

    # Check AJAX
    ajax_req = rf.get(f"/admin-dashboard/?grouping={g}", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
    ajax_req.user = u
    ajax_resp = admin_dashboard_page(ajax_req)
    ajax_data = json.loads(ajax_resp.content.decode("utf-8"))
    chart = ajax_data.get("revenue_chart", {})
    print(f"--- {g.upper()} AJAX ---")
    print("Labels:", chart.get("labels")[:4], "...", chart.get("labels")[-1:])
    print("Count:", len(chart.get("labels", [])))
