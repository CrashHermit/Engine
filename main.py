import asyncio
import sys
from pathlib import Path

# Application modules live under src/
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from engine import Engine

if __name__ == "__main__":
    engine = Engine()
    asyncio.run(engine.run())
