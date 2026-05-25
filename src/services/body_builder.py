from arcadedb_embedded.graph import Vertex
from core.model.part import Shape, Status, SizeScale
from database.repository.part import PartRepository


class BodyBuilderService:
    def __init__(self, part_repo: PartRepository) -> None:
        self.part_repo: PartRepository = part_repo

    def build_body(self, character: Vertex) -> None:
        with self.part_repo.transaction():
            
            head: Vertex = self.part_repo.add_part(character=character, name="head", length=SizeScale.SMALL, width=SizeScale.SMALL, height=SizeScale.SMALL, shape=Shape.SPHERICAL, status=Status.NORMAL, description="The head of the character")
            neck: Vertex = self.part_repo.add_part(character=character, name="neck", length=SizeScale.SMALL, width=SizeScale.SMALL, height=SizeScale.SMALL, shape=Shape.CUBOID, status=Status.NORMAL, description="The neck of the character")
            upper_torso: Vertex = self.part_repo.add_part(character=character, name="upper_torso", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The upper torso of the character")
            lower_torso: Vertex = self.part_repo.add_part(character=character, name="lower_torso", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The lower torso of the character")
            left_upper_arm: Vertex = self.part_repo.add_part(character=character, name="left_upper_arm", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The left upper arm of the character")
            right_upper_arm: Vertex = self.part_repo.add_part(character=character, name="right_upper_arm", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The right upper arm of the character")
            left_forearm: Vertex = self.part_repo.add_part(character=character, name="left_forearm", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The left forearm of the character")
            right_forearm: Vertex = self.part_repo.add_part(character=character, name="right_forearm", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The right forearm of the character")
            left_hand: Vertex = self.part_repo.add_part(character=character, name="left_hand", length=SizeScale.SMALL, width=SizeScale.SMALL, height=SizeScale.SMALL, shape=Shape.SPHERICAL, status=Status.NORMAL, description="The left hand of the character")
            right_hand: Vertex = self.part_repo.add_part(character=character, name="right_hand", length=SizeScale.SMALL, width=SizeScale.SMALL, height=SizeScale.SMALL, shape=Shape.SPHERICAL, status=Status.NORMAL, description="The right hand of the character")
            left_thigh: Vertex = self.part_repo.add_part(character=character, name="left_thigh", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The left thigh of the character")
            right_thigh: Vertex = self.part_repo.add_part(character=character, name="right_thigh", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The right thigh of the character")
            left_shin: Vertex = self.part_repo.add_part(character=character, name="left_shin", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The left shin of the character")
            right_shin: Vertex = self.part_repo.add_part(character=character, name="right_shin", length=SizeScale.MEDIUM, width=SizeScale.MEDIUM, height=SizeScale.MEDIUM, shape=Shape.CUBOID, status=Status.NORMAL, description="The right shin of the character")
            left_foot: Vertex = self.part_repo.add_part(character=character, name="left_foot", length=SizeScale.SMALL, width=SizeScale.SMALL, height=SizeScale.SMALL, shape=Shape.SPHERICAL, status=Status.NORMAL, description="The left foot of the character")
            right_foot: Vertex = self.part_repo.add_part(character=character, name="right_foot", length=SizeScale.SMALL, width=SizeScale.SMALL, height=SizeScale.SMALL, shape=Shape.SPHERICAL, status=Status.NORMAL, description="The right foot of the character")
            
            self.part_repo.attach(source=head, target=upper_torso)
            self.part_repo.attach(source=head, target=neck)
            self.part_repo.attach(source=neck, target=upper_torso)
            self.part_repo.attach(source=upper_torso, target=lower_torso)
            self.part_repo.attach(source=upper_torso, target=left_upper_arm)
            self.part_repo.attach(source=upper_torso, target=right_upper_arm)
            self.part_repo.attach(source=lower_torso, target=left_thigh)
            self.part_repo.attach(source=lower_torso, target=right_thigh)
            self.part_repo.attach(source=left_thigh, target=left_shin)
            self.part_repo.attach(source=left_shin, target=left_foot)
            self.part_repo.attach(source=right_thigh, target=right_shin)
            self.part_repo.attach(source=right_shin, target=right_foot)
            self.part_repo.attach(source=left_upper_arm, target=left_forearm)
            self.part_repo.attach(source=right_upper_arm, target=right_forearm)
            self.part_repo.attach(source=left_forearm, target=left_hand)
            self.part_repo.attach(source=right_forearm, target=right_hand)