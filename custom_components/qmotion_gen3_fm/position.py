"""Translate one-way QSync commanded positions to Home Assistant conventions."""

def qsync_to_ha(qsync_position: int) -> int | None:
    """0=open, 100=closed on QSync. Unknown values stay unknown."""
    if not isinstance(qsync_position, int) or not 0 <= qsync_position <= 100:
        return None
    return 100 - qsync_position


def ha_to_qsync(ha_position: int) -> int:
    """0=closed, 100=open on Home Assistant."""
    if not isinstance(ha_position, int) or not 0 <= ha_position <= 100:
        raise ValueError("Home Assistant cover position must be 0..100")
    return 100 - ha_position
