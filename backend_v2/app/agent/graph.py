from langgraph.graph import END, StateGraph
from app.agent.state import AgentState
from app.agent.nodes import AgentNodes

class GraphBuilder:
    def __init__(self, nodes: AgentNodes):
        self.nodes = nodes

    def build(self):
        workflow = StateGraph(AgentState)

        # Define Nodes
        workflow.add_node("retrieve", self.nodes.retrieve)
        workflow.add_node("grade_documents", self.nodes.grade_documents)
        workflow.add_node("generate", self.nodes.generate)
        # workflow.add_node("rewrite_query", self.nodes.rewrite_query) # Future expansion

        # Define Edges
        workflow.set_entry_point("retrieve")
        
        workflow.add_edge("retrieve", "grade_documents")
        
        # Conditional Logic for "Decide to Generate or Give Up"
        def decide_to_generate(state):
            if not state["documents"]:
                # In a full impl, we would loop to "rewrite_query" here
                # For v2 MVP, we go to generate which handles the "No context" case gracefully
                return "generate"
            return "generate"

        workflow.add_conditional_edges(
            "grade_documents",
            decide_to_generate,
            {
                "generate": "generate",
                # "rewrite": "rewrite_query" 
            }
        )
        
        workflow.add_edge("generate", END)

        return workflow.compile()