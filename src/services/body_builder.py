from arcadedb_embedded.graph import Vertex

from src.core.model.part import Shape, Status, SizeScale
from src.database.repository.base import BaseRepository
from src.database.repository.part import PartRepository


class BodyBuilderService:
    def __init__(self, base: BaseRepository) -> None:
        self._base = base
        self._part_repo = PartRepository(base)

    def build_body(self, character: Vertex) -> None:
        with self._base.transaction():
            head = self._part_repo.add_part(character=character, name="head", length=SizeScale.SMALL, width=SizeScale.SMALL, height=SizeScale.SMALL, shape=Shape.SPHERICAL, status=Status.NORMAL, description="The head of the character")
            neck = self._part_repo.add_part(character=character, name="neck", length=SizeScale.SMALL, width=SizeScale.SMALL, height=SizeScale.SMALL, shape=Shape.CUBOID, status=Status.NORMAL, description="The neck of the character")
            upper_torso = self._part_repo.add_part(character=character, name="upper_torso", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The upper torso of the character")
            lower_torso = self._part_repo.add_part(character=character, name="lower_torso", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The lower torso of the character")
            left_upper_arm = self._part_repo.add_part(character=character, name="left_upper_arm", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The left upper arm of the character")
            right_upper_arm = self._part_repo.add_part(character=character, name="right_upper_arm", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The right upper arm of the character")
            left_forearm = self._part_repo.add_part(character=character, name="left_forearm", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The left forearm of the character")
            right_forearm = self._part_repo.add_part(character=character, name="right_forearm", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The right forearm of the character")
            left_hand = self._part_repo.add_part(character=character, name="left_hand", length=SizeScale.SMALL, width=SizeScale.SMALL, height=SizeScale.SMALL, shape=Shape.SPHERICAL, status=Status.NORMAL, description="The left hand of the character")
            right_hand = self._part_repo.add_part(character=character, name="right_hand", length=SizeScale.SMALL, width=SizeScale.SMALL, height=SizeScale.SMALL, shape=Shape.SPHERICAL, status=Status.NORMAL, description="The right hand of the character")
            left_thigh = self._part_repo.add_part(character=character, name="left_thigh", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The left thigh of the character")
            right_thigh = self._part_repo.add_part(character=character, name="right_thigh", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The right thigh of the character")
            left_shin = self._part_repo.add_part(character=character, name="left_shin", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The left shin of the character")
            right_shin = self._part_repo.add_part(character=character, name="right_shin", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The right shin of the character")
            left_foot = self._part_repo.add_part(character=character, name="left_foot", length=SizeScale.SMALL, width=SizeScale.SMALL, height=SizeScale.SMALL, shape=Shape.SPHERICAL, status=Status.NORMAL, description="The left foot of the character")
            right_foot = self._part_repo.add_part(character=character, name="right_foot", length=SizeScale.SMALL, width=SizeScale.SMALL, height=SizeScale.SMALL, shape=Shape.SPHERICAL, status=Status.NORMAL, description="The right foot of the character")

            self._part_repo.attach(source=head, target=upper_torso)
            self._part_repo.attach(source=head, target=neck)
            self._part_repo.attach(source=neck, target=upper_torso)
            self._part_repo.attach(source=upper_torso, target=lower_torso)
            self._part_repo.attach(source=upper_torso, target=left_upper_arm)
            self._part_repo.attach(source=upper_torso, target=right_upper_arm)
            self._part_repo.attach(source=lower_torso, target=left_thigh)
            self._part_repo.attach(source=lower_torso, target=right_thigh)
            self._part_repo.attach(source=left_thigh, target=left_shin)
            self._part_repo.attach(source=left_shin, target=left_foot)
            self._part_repo.attach(source=right_thigh, target=right_shin)
            self._part_repo.attach(source=right_shin, target=right_foot)
            self._part_repo.attach(source=left_upper_arm, target=left_forearm)
            self._part_repo.attach(source=right_upper_arm, target=right_forearm)
            self._part_repo.attach(source=left_forearm, target=left_hand)
            self._part_repo.attach(source=right_forearm, target=right_hand)
