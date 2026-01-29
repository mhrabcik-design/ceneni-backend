from sqlalchemy import create_engine
import os

paths = [
    "sqlite:///Input/04_Databaze/prices_v2.db",
    "sqlite:///./Input/04_Databaze/prices_v2.db",
    f"sqlite:///{os.path.abspath('Input/04_Databaze/prices_v2.db').replace('\\', '/')}",
    r"sqlite:///Input\04_Databaze\prices_v2.db"
]

for p in paths:
    try:
        print(f"Testing: {p}")
        e = create_engine(p)
        c = e.connect()
        print("  -> SUCCESS")
        c.close()
    except Exception as e:
        print(f"  -> FAIL: {e}")
