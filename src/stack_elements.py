from dataclasses import dataclass

@dataclass(eq=False)
class StackElem:
    def __eq__(self, other):
        return isinstance(self, other)

@dataclass(eq=False)
class Procedure(StackElem):
    name: str
    tag: int

@dataclass(eq=False)
class If(StackElem):
    no: bool
    symbol_check: bool
    check: int
    tag: int
    code_block: bool
    else_check: bool

@dataclass(eq=False)
class ForLoop(StackElem):
    tag: int
    iterations: int

@dataclass(eq=False)
class WriteCommand(StackElem):
    tag: int

@dataclass(eq=False)
class CodeBlock(StackElem):
    started: bool
    multiline: bool
    tag: int
