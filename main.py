import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout
import matplotlib.pyplot as plt
from typing import Tuple
import codeflow.parser as parser
from tree.nodes import ProgramNode,LogicalNode,InstructionNode,LoopNode,BranchNode,WithNode,TryNode
from tree.graph_builder import build_graph
from pathlib import Path
from json import dump

class Maggigy:
    def __init__(self) -> None:
        self._logic_parser = parser.CodeFlowParser()

    def parse_file(self, path: str) ->Tuple[ProgramNode,nx.DiGraph,dict]:
        path_object = Path(path)
        if not path_object.exists():
            raise Exception(f"Path '{path_object.absolute}' doesn't exist")
        elif not path_object.is_file():
            raise Exception(f"Path '{path_object.absolute}' is not a file")
        elif path_object.suffix != '.py':
            raise Exception(f"File '{path_object.absolute}' is not a .py file")
        
        with open(file_path,'r') as f:
            return self._logic_parser.parse(f.read())
    
    def build_json(self, node: LogicalNode):
        match node:
            case InstructionNode():
                return {
                    'type': 'instruction',
                    'value': node.key
                }
            case LoopNode():
                children = []

                for child in node.children:
                    children.append(self.build_json(child))
                return {
                    'type': 'loop',
                    'value': {node.key : children}
                }
            case BranchNode():
                return {
                    'type': 'branch',
                    'value': {
                        condition: [self.build_json(child) for child in children]
                        for condition,children in node.children.items()
                    }
                }
            case TryNode():
                return {
                    'type': 'try-except',
                    'value':  {
                        'try': [self.build_json(child) for child in node.children['_try']],
                        'exceptions': {
                            exception: [self.build_json(child) for child in children]
                            for exception, children in node.children['_except'].items()
                        },
                        'else': [self.build_json(child) for child in node.children['_else']],
                        'finally': [self.build_json(child) for child in node.children['_finally']],
                    }
                }
            case WithNode():
                return {
                    'type': 'with',
                    'value': str(node)
                }
            case _:
                raise TypeError(f"Unsupported node type '{type(node)}'")

            
    def export_tree(self,program: ProgramNode,path: str) -> None:
        json_tree = []

        for node in program.children:
            json_tree.append(self.build_json(node))

        with open(path,'w') as f:
            dump(json_tree,f)

    def display_graph(self, program: ProgramNode):
        graph = build_graph(program)
        pos = graphviz_layout(graph, prog="dot")
        labels = nx.get_node_attributes(graph, 'label')


        # Draw the graph
        plt.figure(figsize=(20, 20))

        nx.draw_networkx_edges(
            graph,
            pos,
            arrows=True,
            arrowstyle='-|>',
            arrowsize=20,
        )


        nx.draw_networkx_labels(
            graph,
            pos,
            labels=labels,
            font_size=10,
            bbox=dict(
                boxstyle='square,pad=0.5',
                facecolor='lightblue',
                edgecolor='black',
            )
        )

        plt.axis('off')
        plt.show()

        input()

if __name__ == '__main__':
    file_path = './example.py'
    
    maggi = Maggigy()

    program_node, graph, grap_labels = maggi.parse_file(file_path)

    program_node.printProgram()

    maggi.export_tree(program_node,'./export.json')




