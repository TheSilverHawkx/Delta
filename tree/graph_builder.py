import networkx as nx
from typing import List
from .nodes import LogicalNode, InstructionNode, LoopNode,BranchNode,WithNode,TryNode,ProgramNode

def build_graph(program: ProgramNode) -> nx.DiGraph:
    graph = nx.DiGraph()

    def add_edges_for_node(node, parent_scope):
        node_id = id(node)
        graph.add_node(node_id, label=str(node))
        
        # Handle different node types
        if isinstance(node, InstructionNode):
            # Link to the next node in the parent scope
            add_next_edge(node, parent_scope)

        elif isinstance(node, LoopNode):
            # Connect all children in the body sequentially
            for i, child in enumerate(node.children):
                child_id = id(child)
                graph.add_node(child_id, label=str(child))
                if i > 0:
                    graph.add_edge(id(node.children[i - 1]), child_id)
                add_edges_for_node(child, node.children)
            # Link the last child to the next node in parent scope
            if node.children:
                add_next_edge(node.children[-1], parent_scope,node)

        elif isinstance(node, BranchNode):
            # For each condition, link nodes in the branch sequentially
            for condition, children in node.children.items():
                for i, child in enumerate(children):
                    child_id = id(child)
                    graph.add_node(child_id, label=f"{condition}: {str(child)}")
                    if i > 0:
                        graph.add_edge(id(children[i - 1]), child_id)
                    add_edges_for_node(child, children)
                # Link the last child of each branch to the next node in parent scope
                if children:
                    add_next_edge(children[-1], parent_scope,node)

        elif isinstance(node, TryNode):
            # Add edges for 'body'
            body = node.children['_try']
            exceptions = node.children['_except']
            else_body = node.children['_else']
            finally_body = node.children['_finally']

            # Handle try block
            for i, child  in enumerate(body):
                child_id = id(child)
                graph.add_node(child_id, label=str(child))

                if i > 0:
                    graph.add_edge(id(body[i - 1]), child_id)
                add_edges_for_node(child, body)

            # Handle else block
            if else_body:
                for i, child  in enumerate(else_body):
                    child_id = id(child)
                    graph.add_node(child_id, label=str(child))

                    if i > 0:
                        graph.add_edge(id(else_body[i - 1]), child_id)
                    add_edges_for_node(child, else_body)
                
                graph.add_edge(id(body[-1]),id(else_body[0]))

            # Handle except blocks
            for exception, except_nodes in exceptions.items():
                for i, child in enumerate(except_nodes):
                    child_id = id(child)
                    graph.add_node(child_id, label=f"except {exception}: {str(child)}")
                    if i > 0:
                        graph.add_edge(id(except_nodes[i - 1]), child_id)
                    add_edges_for_node(child, except_nodes)
            

            # Handle finally block
            if finally_body:
                for i, child in enumerate(finally_body):
                    child_id = id(child)
                    graph.add_node(child_id, label=f"finally: {str(child)}")
                    if i > 0:
                        graph.add_edge(id(finally_body[i - 1]), child_id)
                    add_edges_for_node(child, finally_body)
                add_next_edge(finally_body[-1], parent_scope,node)

                if else_body:
                    graph.add_edge(id(else_body[-1]), id(finally_body[0]))
                else:
                    graph.add_edge(id(body[-1]), id(finally_body[0]))

                if len(exceptions) > 0:
                    for except_nodes in exceptions.values():
                        graph.add_edge(id(except_nodes[-1]),id(finally_body[0]))

        elif isinstance(node, WithNode):
            # Connect all children in the with body sequentially
            for i, child in enumerate(node.children):
                child_id = id(child)
                graph.add_node(child_id, label=str(child))
                if i > 0:
                    graph.add_edge(id(node.children[i - 1]), child_id)
                add_edges_for_node(child, node.children)
            # Link the last child to the next node in parent scope
            if node.children:

                add_next_edge(node.children[-1], parent_scope)

    def add_next_edge(node: LogicalNode, parent_scope: List[LogicalNode],parent_node: LogicalNode = None):
        # Find the next node in the parent scope and link to it
        if parent_scope:
            node_index = parent_scope.index(node) if parent_node is None else parent_scope.index(parent_node)
            if node_index + 1 < len(parent_scope):
                next_node = parent_scope[node_index + 1]
                graph.add_edge(id(node), id(next_node))

    # Start with the ProgramNode and its nodes
    for node in program.children:
        add_edges_for_node(node, program.children)

    return graph
