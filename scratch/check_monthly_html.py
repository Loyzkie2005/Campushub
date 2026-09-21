import os, sys, django, json
sys.path.insert(0, r"c:\Users\leste\Desktop\CAMPUSHUB\backend\core")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.test import Client
from accounts.models import User

u = User.objects.get(username="2023304612")
c = Client()
c.force_login(u)

for g in ["daily", "weekly", "monthly"]:
    res = c.get(f"/admin-dashboard/?grouping={g}")
    html = res.content.decode("utf-8")
    for line in html.splitlines():
        if "salesTrendChartData" in line:
            raw = line.split('application/json">')[1].split("</script>")[0]
            d = json.loads(raw)
            print(f"[{g.upper()}] labels count: {len(d['labels'])} -> {d['labels'][:3]} ... {d['labels'][-2:]}")
        if "dash-card-subtitle" in line and "View" in line:
            print(f"[{g.upper()}] subtitle: {line.strip()}")
