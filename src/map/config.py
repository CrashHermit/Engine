from dataclasses import dataclass


@dataclass
class GridConfig:
    rows: int = 50
    cols: int = 80


@dataclass
class HeightmapConfig:
    # Controls feature size — lower = broader continents, higher = smaller islands
    scale: float = 3.0
    # Noise layers stacked on top of each other; more = finer detail
    octaves: int = 6
    # How quickly amplitude fades per octave; higher = rougher terrain
    persistence: float = 0.5
    # How quickly frequency increases per octave; standard is 2.0
    lacunarity: float = 2.0
    # Elevation threshold (0-100) below which a tile is ocean
    sea_level: int = 45
    # Seed for reproducibility; 0 = random-ish default
    seed: int = 0
