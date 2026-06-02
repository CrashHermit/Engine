from dspy import InputField, OutputField, Signature

from src.core.model.entity import EntityStance


class EngagementSignature(Signature):
    """
    Decide a creature's engagement posture toward the player for this turn —
    both first contact (aggro) and a neutralized foe re-engaging use this one
    judgment. Given the creature's nature, its current situation, and what the
    player just did, choose its new posture:

    - hostile: it acts against the player NOW (strikes, attacks, re-engages).
    - wary: it has noticed and is tense/poised, but has NOT committed to attack.
    - unaware: no change — it remains oblivious or stays withdrawn.

    Judge from the creature's nature and the fiction. A predatory or territorial
    creature turns hostile when the player gets close, encroaches, attacks it,
    or makes itself obvious; it may pass through wary first if contact is faint.
    A neutral, friendly, or skittish creature does NOT turn hostile on its own
    (a skittish one would rather flee). A creature the player directly attacks or
    provokes is hostile. Be conservative for ambient, decisive on real provocation.
    """

    creature: str = InputField(description="The creature")
    nature: str = InputField(description="Its disposition (predatory/territorial/guardian/skittish/neutral/friendly)")
    situation: str = InputField(description="Its current posture/status and any re-engage condition")
    player_action: str = InputField(description="What the player just did this turn")
    recent_events: str = InputField(default="", description="Recent narration, for context")

    posture: EntityStance = OutputField(description="New posture: hostile / wary / unaware")
