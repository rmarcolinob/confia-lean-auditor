"""P1 entry point; framing/extraction is shared without changing its contract."""
from .digital_items import DigitalItemClaims, collect_digital_items

PROBLEM_ID = "TME2_P1_PILOT"


def collect_tme2_p1_digital(items):
    return collect_digital_items(PROBLEM_ID, items)
