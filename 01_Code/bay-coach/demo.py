"""Bay Coach — offline demo.  Run:  python demo.py"""

import engine


def main() -> int:
    vehicle = engine.Vehicle(
        current_mileage=68_400, year=2019, make="Toyota", model="Camry",
        history=[
            engine.ServiceRecord("Oil & filter change", 62_000),
            engine.ServiceRecord("Tire rotation", 62_000),
            engine.ServiceRecord("Brake inspection", 55_000),
            engine.ServiceRecord("Transmission fluid", 0),   # never done since new
        ],
    )
    result = engine.recommend(vehicle)
    print(engine.render_writeup_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
