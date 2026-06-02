from src.state import GraphState

class CandidateSourcesNode:
    async def __call__(self, state: GraphState) -> dict:
        sources = [e.name for e in state.scene_entities] + ["environment"]
        return {"_candidate_sources": sources}