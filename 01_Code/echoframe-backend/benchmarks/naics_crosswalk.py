"""
EchoFrame — industry -> NAICS crosswalk
─────────────────────────────────────────────────────────────────────────────
Maps every industry key used in clarity_engine.INDUSTRY_BENCHMARKS to a NAICS
code, so the benchmark fetch scripts (fetch_bls_qcew.py, fetch_census_cbp.py,
fetch_irs_soi.py) know which government series to pull for each industry.

Two NAICS fields per industry, because the sources differ in granularity:

  naics_6  — 6-digit code, used for BLS QCEW and Census CBP. Both support
             real 6-digit industry detail (down to the county level for
             QCEW), so this can be as specific as NAICS allows.

  naics_sector — the coarser sector/major-group bucket IRS SOI publishes at
             (its public tables don't go to 6-digit). Several of our
             industries will share one soi bucket — that's a source
             limitation, not a mapping mistake.

THIS IS A FIRST DRAFT. NAICS codes below are standard/public codes I'm
confident in, but Jacob should sanity check the groupings, especially where
several EchoFrame industries collapse into one naics_sector (that's where
the IRS ratio will be least specific to any one of them).
"""

from __future__ import annotations

# key: EchoFrame industry key (must match clarity_engine.INDUSTRY_BENCHMARKS)
# value: {"naics_6": "######", "naics_sector": "##", "label": "human readable"}
CROSSWALK: dict[str, dict] = {
    "restaurant":              {"naics_6": "722511", "naics_sector": "72", "label": "Full-Service Restaurants"},
    "fast food / qsr":         {"naics_6": "722513", "naics_sector": "72", "label": "Limited-Service Restaurants"},
    "coffee shop / café":      {"naics_6": "722515", "naics_sector": "72", "label": "Snack and Nonalcoholic Beverage Bars"},
    "bar / nightclub":         {"naics_6": "722410", "naics_sector": "72", "label": "Drinking Places (Alcoholic Beverages)"},
    "food truck":              {"naics_6": "722330", "naics_sector": "72", "label": "Mobile Food Services"},
    "catering":                {"naics_6": "722320", "naics_sector": "72", "label": "Caterers"},
    "bakery":                  {"naics_6": "311811", "naics_sector": "31-33", "label": "Retail Bakeries"},

    "retail":                  {"naics_6": "455211", "naics_sector": "44-45", "label": "Department Stores"},
    "clothing / apparel":      {"naics_6": "458110", "naics_sector": "44-45", "label": "Clothing Stores"},
    "grocery / market":        {"naics_6": "445110", "naics_sector": "44-45", "label": "Supermarkets and Grocery Stores"},
    "sporting goods":          {"naics_6": "459110", "naics_sector": "44-45", "label": "Sporting Goods Stores"},
    "electronics retail":      {"naics_6": "443142", "naics_sector": "44-45", "label": "Electronics Stores"},
    "jewelry / accessories":   {"naics_6": "459940", "naics_sector": "44-45", "label": "Jewelry Stores"},
    "pet store":               {"naics_6": "459910", "naics_sector": "44-45", "label": "Pet and Pet Supplies Stores"},
    "auto parts store":        {"naics_6": "441330", "naics_sector": "44-45", "label": "Automotive Parts and Accessories Stores"},

    "salon/spa":               {"naics_6": "812112", "naics_sector": "81", "label": "Beauty Salons"},
    "salon / spa":             {"naics_6": "812112", "naics_sector": "81", "label": "Beauty Salons"},
    "barbershop":              {"naics_6": "812111", "naics_sector": "81", "label": "Barber Shops"},
    "gym / fitness studio":    {"naics_6": "713940", "naics_sector": "71", "label": "Fitness and Recreational Sports Centers"},
    "yoga / pilates studio":   {"naics_6": "713940", "naics_sector": "71", "label": "Fitness and Recreational Sports Centers"},
    "massage therapy":         {"naics_6": "812199", "naics_sector": "81", "label": "Other Personal Care Services"},
    "physical therapy":        {"naics_6": "621340", "naics_sector": "62", "label": "Offices of Physical, Occupational Therapists"},
    "chiropractor":            {"naics_6": "621310", "naics_sector": "62", "label": "Offices of Chiropractors"},
    "dental practice":         {"naics_6": "621210", "naics_sector": "62", "label": "Offices of Dentists"},
    "medical practice":        {"naics_6": "621111", "naics_sector": "62", "label": "Offices of Physicians"},
    "veterinary clinic":       {"naics_6": "541940", "naics_sector": "54", "label": "Veterinary Services"},
    "pharmacy":                {"naics_6": "446110", "naics_sector": "44-45", "label": "Pharmacies and Drug Stores"},

    "accounting / cpa firm":   {"naics_6": "541211", "naics_sector": "54", "label": "Offices of CPAs"},
    "law firm":                {"naics_6": "541110", "naics_sector": "54", "label": "Offices of Lawyers"},
    "real estate agency":      {"naics_6": "531210", "naics_sector": "53", "label": "Offices of Real Estate Agents and Brokers"},
    "insurance agency":        {"naics_6": "524210", "naics_sector": "52", "label": "Insurance Agencies and Brokerages"},
    "financial advisory":      {"naics_6": "523930", "naics_sector": "52", "label": "Investment Advice"},
    "consulting firm":         {"naics_6": "541611", "naics_sector": "54", "label": "Administrative Management Consulting"},
    "staffing / recruiting":   {"naics_6": "561312", "naics_sector": "56", "label": "Executive Search Services"},

    "hvac":                    {"naics_6": "238220", "naics_sector": "23", "label": "Plumbing, Heating, and Air-Conditioning Contractors"},
    "plumbing":                {"naics_6": "238220", "naics_sector": "23", "label": "Plumbing, Heating, and Air-Conditioning Contractors"},
    "electrical":              {"naics_6": "238210", "naics_sector": "23", "label": "Electrical Contractors"},
    "landscaping / lawn care": {"naics_6": "561730", "naics_sector": "56", "label": "Landscaping Services"},
    "cleaning service":        {"naics_6": "561720", "naics_sector": "56", "label": "Janitorial Services"},
    "general contractor":      {"naics_6": "236220", "naics_sector": "23", "label": "Commercial Building Construction"},
    "pest control":            {"naics_6": "561710", "naics_sector": "56", "label": "Pest Control Services"},
    "moving company":          {"naics_6": "484210", "naics_sector": "48-49", "label": "Used Household Goods Moving"},
    "pool service":            {"naics_6": "561790", "naics_sector": "56", "label": "Other Building/Dwelling Services (pool cleaning)"},
    "roofing":                 {"naics_6": "238160", "naics_sector": "23", "label": "Roofing Contractors"},
    "painting":                {"naics_6": "238320", "naics_sector": "23", "label": "Painting and Wall Covering Contractors"},

    "auto repair / mechanic":  {"naics_6": "811111", "naics_sector": "81", "label": "General Automotive Repair"},
    "car wash / detailing":    {"naics_6": "811192", "naics_sector": "81", "label": "Car Washes"},
    "auto dealership":         {"naics_6": "441110", "naics_sector": "44-45", "label": "New Car Dealers"},
    "tire shop":               {"naics_6": "441320", "naics_sector": "44-45", "label": "Tire Dealers"},
    "towing":                  {"naics_6": "488410", "naics_sector": "48-49", "label": "Motor Vehicle Towing"},

    "digital/saas":            {"naics_6": "511210", "naics_sector": "51", "label": "Software Publishers"},
    "digital / saas":          {"naics_6": "511210", "naics_sector": "51", "label": "Software Publishers"},
    "it services / msp":       {"naics_6": "541513", "naics_sector": "54", "label": "Computer Facilities Management (MSP)"},
    "marketing agency":        {"naics_6": "541810", "naics_sector": "54", "label": "Advertising Agencies"},
    "web design / dev agency": {"naics_6": "541511", "naics_sector": "54", "label": "Custom Computer Programming Services"},
    "e-commerce":              {"naics_6": "454110", "naics_sector": "44-45", "label": "Electronic Shopping and Mail-Order Houses"},
    "social media management": {"naics_6": "541810", "naics_sector": "54", "label": "Advertising Agencies"},

    "daycare / preschool":     {"naics_6": "624410", "naics_sector": "62", "label": "Child Day Care Services"},
    "tutoring / learning center": {"naics_6": "611691", "naics_sector": "61", "label": "Exam Prep and Tutoring"},
    "music / dance studio":    {"naics_6": "611610", "naics_sector": "61", "label": "Fine Arts Schools"},
    "martial arts studio":     {"naics_6": "611620", "naics_sector": "61", "label": "Sports and Recreation Instruction"},
    "private school":          {"naics_6": "611110", "naics_sector": "61", "label": "Elementary and Secondary Schools"},

    "hotel / motel":           {"naics_6": "721110", "naics_sector": "72", "label": "Hotels (except Casino Hotels) and Motels"},
    "vacation rental / airbnb": {"naics_6": "721199", "naics_sector": "72", "label": "All Other Traveler Accommodation"},
    "event venue":             {"naics_6": "531120", "naics_sector": "53", "label": "Lessors of Nonresidential Buildings"},
    "photography studio":      {"naics_6": "541921", "naics_sector": "54", "label": "Photography Studios, Portrait"},
    "videography":             {"naics_6": "512110", "naics_sector": "51", "label": "Motion Picture and Video Production"},
    "wedding / event planning": {"naics_6": "561920", "naics_sector": "56", "label": "Convention and Trade Show Organizers (events)"},

    "laundromat / dry cleaning": {"naics_6": "812310", "naics_sector": "81", "label": "Coin-Operated Laundries and Drycleaners"},
    "self storage":            {"naics_6": "531130", "naics_sector": "53", "label": "Lessors of Miniwarehouses and Self-Storage"},
    "printing / signage":      {"naics_6": "323111", "naics_sector": "31-33", "label": "Commercial Printing"},
    "trucking / logistics":    {"naics_6": "484121", "naics_sector": "48-49", "label": "General Freight Trucking, Long-Distance"},
    "construction materials":  {"naics_6": "444190", "naics_sector": "44-45", "label": "Other Building Material Dealers"},
}


def get_naics(industry_key: str) -> dict | None:
    """Look up the NAICS crosswalk entry for an EchoFrame industry key.
    Returns None if the industry isn't mapped yet (fetch scripts should skip,
    loader.py falls back to the existing hardcoded estimate)."""
    return CROSSWALK.get(industry_key.strip().lower())


def unmapped(industry_keys: list[str]) -> list[str]:
    """Given a list of industry keys (e.g. from INDUSTRY_BENCHMARKS), return
    the ones with no crosswalk entry yet. Used by a startup check / test."""
    return [k for k in industry_keys if get_naics(k) is None]
