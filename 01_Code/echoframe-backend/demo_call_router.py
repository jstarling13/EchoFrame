"""Offline demo for Call Router. python demo_call_router.py"""
from pathlib import Path
from call_router_engine import render_from_csv

CSV = Path(__file__).resolve().parent / "demo_output" / "call_router_sample_input.csv"

PROSE = {
    "after_hours_note": [
        "Of the 21 calls that landed outside business hours this week, <b>every one was answered live</b> — "
        "none dropped to voicemail. Call Router qualifies each by urgency: true emergencies (buzzing breakers, "
        "partial outages, burning smells) trigger an immediate SMS to the on-call tech with the caller's name, "
        "address, and symptom, while non-urgent estimate requests are captured and added to the next-morning "
        "call-back list so techs aren't woken for a deck-lighting quote.",
        "Industry data is blunt on this: <b>roughly 1 in 4 service calls comes in after hours</b>, and the "
        "average homeowner with an electrical problem calls the next contractor within minutes if no one picks "
        "up. The 21 captured calls represent demand that, on a voicemail-only line, would have largely been lost "
        "to a competitor before morning.",
    ],
    "one_thing_title": "The after-hours calls alone were worth about $14,200 in booked work this week.",
    "one_thing_body": (
        "The 21 captured after-hours calls converted into <span class=\"dollar\">11 booked jobs</span> — a mix of "
        "two emergency panel/breaker repairs (~$1,800 each), service calls (~$350 each), and two larger "
        "estimate-stage jobs (an EV charger and a panel upgrade) that started with an after-hours call. At a "
        "conservative blended value, that's roughly <span class=\"dollar\">$14,200</span> in work that, on a "
        "voicemail-only line, would most likely have gone to the next contractor before you opened. Over a year, "
        "that single capture rate is the difference between a busy schedule and a leaking one — worth on the order "
        "of <span class=\"dollar\">$70K+</span> in recovered annual revenue."
    ),
}


def main():
    print(f"  call-router -> {render_from_csv(CSV, prose=PROSE, is_sample=True)}")


if __name__ == "__main__":
    main()
