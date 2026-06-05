    
from enum import StrEnum


class Humidity(StrEnum):
    ARID: str = "arid"  # bone-dry desert air; dust hangs; lips crack
    DRY: str = "dry"  # noticeably dry air
    CRISP: str = "crisp"  # dry but fresh; sharp, clear air
    MILD: str = "mild"  # comfortable, balanced; anchor (shared with temperature)
    HUMID: str = "humid"  # moist air you can feel
    MUGGY: str = "muggy"  # sticky, heavy, oppressive
    SOAKING: str = "soaking"  # saturated air; monsoon-thick; rain-soaked world