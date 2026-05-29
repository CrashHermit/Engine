from dspy import InputField, OutputField, Signature

from src.core.model.resolution import Attribute


class ThreatChannelClassifierSignature(Signature):
    """
    Choose which attribute a character would use to RESIST the threat looming over
    this beat — its channel (decision #15). This is about weathering the
    consequence, which may differ from the attribute used to attempt the beat:

      - corpus: shrug off / endure a physical blow or strain.
      - mens:   see it coming, out-think, or stay sharp.
      - anima:  steel the nerve, resist fear / influence / the uncanny.

    Judge from the beat and its situation alone (this runs in parallel with the
    other framing classifiers). Pick the single attribute that best fits how one
    would resist what could go wrong here.
    """

    character_description: str = InputField(default="", description="A description of the player character")
    location_description: str = InputField(default="", description="A description of the current location")
    entities_at_location: str = InputField(default="", description="Entities present in the current location")
    contested_beat: str = InputField(description="The single action being attempted")

    channel: Attribute = OutputField(description="corpus, mens, or anima — the attribute that resists the looming threat")
