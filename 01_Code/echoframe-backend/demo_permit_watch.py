"""Offline demo for Permit Watch. python demo_permit_watch.py"""
from pathlib import Path
from permit_watch_engine import render_from_csv

CSV = Path(__file__).resolve().parent / "demo_output" / "permit_watch_sample_input.csv"

PROSE = {
    "alerts": [
        {"label": "Van #3 registration",
         "desc": "Vehicle is on the road non-compliant. Renew at GA DRIVES / county tag office today; pull from service until cleared."},
        {"label": "USDOT annual update",
         "desc": "MCS-150 biennial refresh. File online — failure deactivates the USDOT number and grounds the fleet."},
        {"label": "Commercial auto insurance",
         "desc": "Confirm renewal and re-shop now; a lapse voids coverage on all 6 vehicles."},
        {"label": "Master plumber license",
         "desc": "Owner's qualifying-agent license; the company can't pull permits without it active."},
    ],
    "method_note": [
        "Every registration, license, insurance policy, and permit your business holds is logged once with its "
        "renewal date and responsible party. Permit Watch then counts down to each expiry and sends an "
        "<b>automatic alert 30 days out</b> — and again at 14 and 3 days — by email and text, so nothing lapses "
        "because it fell off a calendar.",
        "This fleet has <b>14 items</b> in scope across vehicles, drivers, the entity, and trade licenses. One "
        "has already lapsed, three renew inside 30 days, and the rest are clear for this cycle. <b>Days Until "
        "Due</b> is measured from the report date; negative means the item is already expired.",
    ],
    "one_thing_title": "Renew Van #3's registration today — it's already lapsed.",
    "one_thing_body": (
        "The tag expired <span class=\"dollar\">7 days ago</span>, which means a working service van is on Columbus "
        "roads non-compliant right now. A traffic stop risks a citation, impound, and <span class=\"dollar\">$25+ in "
        "state late penalties</span> on top of the renewal — but the real exposure is your insurer: a claim "
        "involving an unregistered vehicle can be <span class=\"dollar\">denied outright</span>, turning a "
        "fender-bender into an uncovered loss worth tens of thousands. Pull the van from the schedule, renew through "
        "GA DRIVES or the Muscogee County tag office this morning, and it's back on the road by afternoon. Everything "
        "else on this list has runway; this one is bleeding today."
    ),
}


def main():
    print(f"  permit-watch -> {render_from_csv(CSV, prose=PROSE, is_sample=True)}")


if __name__ == "__main__":
    main()
