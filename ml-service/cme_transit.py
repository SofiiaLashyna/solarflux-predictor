import math
from datetime import datetime, timedelta, timezone

AU = 149_597_870.7
RS = 695_700.0


def to_dt(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)


def const_speed_hours(v0, r0_rs=21.5):
    return (AU - r0_rs * RS) / v0 / 3600


def dbm_hours(v0, r0_rs=21.5, w=400.0, gamma=0.2e-7):
    """Drag-based model: dv/dt = -gamma * (v - w) * |v - w|.  v0, w у км/с, gamma у 1/км."""
    target = AU - r0_rs * RS
    sign = 1 if v0 >= w else -1
    dv = abs(v0 - w)
    f = lambda t: w * t + sign * math.log1p(gamma * dv * t) / gamma - target
    lo, hi = 1.0, 30 * 24 * 3600.0
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
    return lo / 3600


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