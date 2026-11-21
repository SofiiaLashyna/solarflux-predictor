from datetime import timedelta

from cme_models import const_speed_hours, dbm_hours, to_dt

t0 = to_dt("2024-05-08T09:30Z")
v0 = 870.0
observed = {"IPS 14:00": to_dt("2024-05-10T14:00Z"), "IPS 16:36": to_dt("2024-05-10T16:36Z")}
enlil = to_dt("2024-05-10T12:14Z")  

print("різниця = оцінка мінус факт (плюс означає, що оцінка пізніша)")
for name, hours in (("стала швидкість", const_speed_hours(v0)), ("drag-based", dbm_hours(v0))):
    est = t0 + timedelta(hours=hours)
    diffs = ", ".join(f"{k}: {(est - t).total_seconds() / 3600:+.1f} год" for k, t in observed.items())
    print(f"{name:16s} політ {hours:5.1f} год -> {est:%d.%m %H:%M} UTC  ({diffs})")
print(f"{'ENLIL':16s} -> {enlil:%d.%m %H:%M} UTC  (" +
      ", ".join(f"{k}: {(enlil - t).total_seconds() / 3600:+.1f} год" for k, t in observed.items()) + ")")