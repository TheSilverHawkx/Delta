from typing import Optional,List,Literal,TypedDict,Any
from collections import OrderedDict
from uuid import uuid4
from pydantic import BaseModel, UUID4, NonNegativeInt
from pathlib import Path

class TreeNode(BaseModel):
     id: UUID4
     children: List['TreeNode']

     def __init__(self):
         super().__init__(id = uuid4(), children=[])

     def __iter__(self):
         return iter(self.children)
     
     def __repr__(self):
         return f"TreeNode({self.id})"
     
     def add_child(self, node: 'TreeNode') -> None:
         self.children.append(node)
     
class DirectoryNode(TreeNode):
    path: Path

    def __init__(self,path: Path):
        self.path = path
        super().__init__()

class FileNode(TreeNode):
    path: Path
    program: 'ProgramNode'

    def __init__(self,path: Path, program: 'ProgramNode'):
        self.path = path
        self.program = program
        super().__init__()

class ProgramNode(TreeNode):   
    def printProgram(self) -> None:
        for node in self.children:
            self._printNode(node)
    
    def _printNode(self, node: 'LogicalNode', depth: int = 0) -> None:
        if isinstance(node, InstructionNode):
            print("  " * depth + str(node))
        
        elif isinstance(node,BranchNode):
            print("  " * depth + f"Branch Node:")
            depth +=1
            for k,children in node.children.items():
                print("  " * depth + f"{k}:")
                for child in children:
                    self._printNode(child,depth+1)
        
        elif isinstance(node,LoopNode):
            print("  " * depth + str(node))
            for child in node.children:
                self._printNode(child,depth+1)

        elif isinstance(node,TryNode):
            print("  " * depth + f"Try Node:")
            depth +=1
            print("  " * depth + f"body:")
            for child in node.children['_try']:
                self._printNode(child,depth+1)

            print("  " * depth + f"excepts:")
            depth +=1
            for k,children in node.children['_except'].items():
                print("  " * depth + f"{k}:")
                for child in children:
                    self._printNode(child,depth+1)

            if node.children['_else']:
                print("  " * depth-1 + f"else:")
                for child in node.else_body:
                    self._printNode(child,depth+1)

            if node.children['_finally']:
                print("  " * depth-1 + f"finally:")
                for child in node.finally_body:
                    self._printNode(child,depth+1)
            
        elif isinstance(node,WithNode):
            print("  " * depth + str(node))
            depth+=1
            for child in node.children:
                    self._printNode(child,depth+1)

class TryNodeChildren(TypedDict):
    _try: List['LogicalNode'] = []
    _except: OrderedDict[str,List['LogicalNode']] = OrderedDict()
    _else: List['LogicalNode'] = []
    _finally: List['LogicalNode'] = []

class LogicalNode(BaseModel):
    key: str | None
    lineno: NonNegativeInt
    col_offset: NonNegativeInt
    children: List['LogicalNode']

    def __init__(self, lineno: int, col_offset: int):
        super().__init__(
            key=None,
            children=[],
            lineno=lineno,
            col_offset=col_offset
        )

    def add_children(self, *nodes):
        self.children.extend(nodes)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.key})"

    def __repr__(self) -> str:
        return self.__str__()

class InstructionNode(LogicalNode):
    def __init__(self, instruction: str, lineno: int, col_offset: int):
        super().__init__(lineno, col_offset)
        self.key: str = instruction

class LoopNode(LogicalNode):
    def __init__(self, condition: str, lineno: int, col_offset: int):
        super().__init__(lineno, col_offset)
        self.key: str = condition
        
class BranchNode(LogicalNode):
    def __init__(self, lineno: int, col_offset: int):
        super().__init__(lineno, col_offset)
        self.children: OrderedDict[Optional[str], List[LogicalNode]] = OrderedDict()
        self.key = ''

    def add_branch(self, condition: Optional[str], nodes: List[LogicalNode]):
        """
        Add a branch to the branch node.

        :param condition: Condition as a string (None for 'else' branch)
        :param node: The LogicalNode that this condition leads to
        """
        self.children[condition] = nodes
        self.key += f", {condition}" if len(self.key) > 0 else condition

class TryNode(LogicalNode):
    def __init__(self, lineno: int, col_offset: int):
        super().__init__(lineno, col_offset)

        self.children: TryNodeChildren = {
            '_try': [],
            '_except': OrderedDict(),
            '_else': [],
            '_finally':  []
        }

    def add_except(self, exception: str, nodes: List[LogicalNode]):
        self.children['_except'][exception] = nodes
        self._update_key()
        

    def _update_key(self):
        self.key = "try,"
        self.key += ",".join(self.children['_except'].keys())
        if len(self.children['_else']) > 0:
            self.key += ", else"
        if len(self.children['_finally']) > 0:
            self.key += ", finally"

    def add_nodes(self, category: Literal['try','else','finally'], nodes: List[LogicalNode]):
        self.children[f"_{category}"].extend(nodes)
        

class WithNode(LogicalNode):
    def __init__(self, context_expr: str, lineno: int, col_offset: int):
        super().__init__(lineno, col_offset)
        self.key: str = context_expr