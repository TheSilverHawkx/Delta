from typing import Tuple, List
from tree.nodes import LogicalNode, InstructionNode, LoopNode,BranchNode,WithNode,TryNode,ProgramNode
import ast
import networkx as nx

class Scope():
    def __init__(self, level: int = 1) -> None:
        self.level = level
        self.nodes: List[LogicalNode] = []
    
    def __repr__(self) -> str:
        return f"Scope(level={self.level},nodesCount={len(self.nodes)})"

class CodeFlowParser(ast.NodeVisitor):
    def __init__(self):
        self.scopes: list[Scope] = [Scope()]
        self.graph = nx.DiGraph()
        self.graph_labels = {}

    def parse(self, source_code: str) -> Tuple[ProgramNode,nx.DiGraph,dict]:
        """
        Parse the source code and build the logic flow graph.
        
        :param source_code: The Python source code as a string.
        :return: The starting LogicalNode of the graph.
        """
        tree = ast.parse(source_code)
        self.visit(tree)
        
        program_node = ProgramNode()
        program_node.children = self.scopes[0].nodes

        return program_node, self.graph,self.graph_labels

    def _stringifyNode(self, node: ast.AST) -> str:
        return ast.unparse(node).strip()

    def _add_node_to_scope(self,node: LogicalNode):
        scope = self.scopes[-1]
        scope.nodes.append(node)  

    def _add_node_to_graph(self,origin: LogicalNode, dest: LogicalNode, label: str = None):
        self.graph.add_edge(origin,dest)

        if label is not None:
            self.graph_labels[(origin,dest)] = label

    def generic_visit(self, node, field: str = None):
        if field is not None:
            value = getattr(node,field)
            if value is None:
                raise Exception(f"Error at line {getattr(node, 'lineno', '?')}, col {getattr(node, 'col_offset', '?')}: field '{field}' not found")
            if isinstance(value,list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item)
            else:
                self.visit(value)
        else:
            super().generic_visit(node)

    def visit_Module(self, node: ast.Module):
        """
        Visit the root module node.
        """
        for stmt in node.body:
            self.visit(stmt)

    def visit_Expr(self, node: ast.Expr):
        """
        Visit an expression node.
        """
        instruction_node = InstructionNode(
            instruction=self._stringifyNode(node),
            lineno=node.lineno,
            col_offset=node.col_offset
        )

        self._add_node_to_scope(instruction_node)

    def visit_Assign(self, node: ast.Assign):
        """
        Visit an assignment node.
        """
        instruction_node = InstructionNode(
            instruction=self._stringifyNode(node),
            lineno=node.lineno,
            col_offset=node.col_offset
        )

        self._add_node_to_scope(instruction_node)

    def visit_AugAssign(self, node: ast.AugAssign):
        """
        Visit an augmented assignment node (e.g., x += 1).
        """
        instruction_node = InstructionNode(
            instruction=self._stringifyNode(node),
            lineno=node.lineno,
            col_offset=node.col_offset
        )

        self._add_node_to_scope(instruction_node)
    
    def visit_If(self, node: ast.If):
        """
        Visit an if statement.
        """
        branch_node = BranchNode(
            lineno=node.lineno,
            col_offset=node.col_offset
        )
        self._add_node_to_scope(branch_node)

        # Handle the 'if' condition
        condition = self._stringifyNode(node.test)
        
        self.scopes.append(Scope(self.scopes[-1].level+1))

        self.generic_visit(node,'body')

        scope = self.scopes.pop()

        branch_node.add_branch(condition, scope.nodes)
        # self._add_node_to_graph(branch_node,scope.nodes,condition)

        # Handle 'elif' and 'else' blocks


        while node.orelse:
            self.scopes.append(Scope(self.scopes[-1].level+1))

            if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                # 'elif' branch
                node = node.orelse[0]
                self.generic_visit(node,'body')
                scope = self.scopes.pop()

                branch_node.add_branch(
                    self._stringifyNode(node.test),
                    scope.nodes
                )
            else:
                # 'else' branch
                self.generic_visit(node,'orelse')
                scope = self.scopes.pop()
                branch_node.add_branch('else', scope.nodes)
                break
        
    def visit_For(self, node: ast.For):
        """
        Visit a for loop.
        """
        loop_node = LoopNode(
            condition=self._stringifyNode(node.target) + " in " + self._stringifyNode(node.iter),
            lineno=node.lineno,
            col_offset=node.col_offset
        )

        self._add_node_to_scope(loop_node)


        # Parse the loop body
        self.scopes.append(Scope(self.scopes[-1].level+1))
        self.generic_visit(node,'body')
        scope = self.scopes.pop()
        loop_node.add_children(*scope.nodes)
        # self._add_node_to_graph(loop_node,scope.nodes,"loop body")

    def visit_While(self, node: ast.While):
        """
        Visit a while loop.
        """
        loop_node = LoopNode(
            condition=self._stringifyNode(node.test),
            lineno=node.lineno,
            col_offset=node.col_offset
        )
        self._add_node_to_scope(loop_node)

        
        # Parse the loop body
        self.scopes.append(Scope(self.scopes[-1].level+1))
        self.generic_visit(node,'body')
        scope = self.scopes.pop()
        loop_node.add_children(*scope.nodes)
        # self._add_node_to_graph(loop_node,scope.nodes,"loop body")

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """
        Visit a function definition.
        """
        pass

    def visit_Return(self, node: ast.Return):
        """
        Visit a return statement.
        """
        self._add_node_to_scope(InstructionNode(
            instruction=self._stringifyNode(node),
            lineno=node.lineno,
            col_offset=node.col_offset
        ))

    def visit_Break(self, node: ast.Break):
        """
        Visit a break statement.
        """
        self._add_node_to_scope(InstructionNode(
            instruction='break',
            lineno=node.lineno,
            col_offset=node.col_offset
        ))

    def visit_Continue(self, node: ast.Continue):
        """
        Visit a continue statement.
        """
        self._add_node_to_scope(InstructionNode(
            instruction='continue',
            lineno=node.lineno,
            col_offset=node.col_offset
        ))

    def visit_Pass(self,node: ast.Pass):
        """
        Visit a pass block.
        """
        self._add_node_to_scope(InstructionNode(
            'pass',
            lineno=node.lineno,
            col_offset=node.col_offset
        ))

    def visit_Try(self, node: ast.Try):
        """
        Visit a try-except block.
        """
        try_node = TryNode(
            lineno=node.lineno,
            col_offset=node.col_offset
        )
        self._add_node_to_scope(try_node)

        # Parse the try block
        self.scopes.append(Scope(self.scopes[-1].level+1))
        self.generic_visit(node,'body')
        scope = self.scopes.pop()
        try_node.add_nodes('try',scope.nodes)
        # self._add_node_to_graph(try_node,scope.nodes,"try")

        # Parse except handlers
        for handler in node.handlers:
            exception_list = []
            if handler.type:
                if isinstance(handler.type, ast.Tuple):
                    # Multiple exceptions
                    for exc in handler.type.elts:
                        exception_str = self._get_exception_str(exc, handler.name)
                        exception_list.append(exception_str)
                else:
                    exception_str = self._get_exception_str(handler.type, handler.name)
                    exception_list.append(exception_str)
            else:
                exception_list.append('all')

            # Parse the except block
            self.scopes.append(Scope(self.scopes[-1].level+1))
            self.generic_visit(handler,'body')
            scope = self.scopes.pop()

            # Add each exception to the excepts dictionary
            for exception_str in exception_list:
                try_node.add_except(exception_str, scope.nodes)
                # self._add_node_to_graph(try_node,scope.nodes,exception_str)

        # Parse else block
        if node.orelse:
            self.scopes.append(Scope(self.scopes[-1].level+1))
            self.generic_visit(node,'orelse')
            scope = self.scopes.pop()
            try_node.add_nodes('else',scope.nodes)
            # self._add_node_to_graph(try_node,scope.nodes,'else')


        # Parse finally block
        if node.finalbody:
            self.scopes.append(Scope(self.scopes[-1].level+1))
            self.generic_visit(node,'finalbody')
            scope = self.scopes.pop()
            try_node.add_nodes('finally',scope.nodes)
            # self._add_node_to_graph(try_node,scope.nodes,'finally')

    def _get_exception_str(self, exc_node, alias):
        """
        Helper method to get the exception string from an exception node and alias.
        """
        exception_type = self._stringifyNode(exc_node)
        if alias:
            exception_str = f"{exception_type} as {alias}"
        else:
            exception_str = exception_type
        return exception_str

    def visit_With(self, node: ast.With):
        """
        Visit a with statement.
        """
        context_exprs = [self._stringifyNode(item) for item in node.items]
        context_expr_str = ', '.join(context_exprs)

        with_node = WithNode(
            context_expr=context_expr_str,
            lineno=node.lineno,
            col_offset=node.col_offset
        )

        # Parse the with block
        self.scopes.append(Scope(self.scopes[-1].level+1))
        self.generic_visit(node, 'body')
        scope = self.scopes.pop()
        with_node.add_children(*scope.nodes)
            
        self.last_node = with_node

    def visit(self, node):
        """
        Override visit to handle exceptions and provide error details.
        """
        try:
            super().visit(node)
        except Exception as e:
            msg = f"Error at line {getattr(node, 'lineno', '?')}, col {getattr(node, 'col_offset', '?')}: {str(e)}"
            raise Exception(msg)