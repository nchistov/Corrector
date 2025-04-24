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
    multiline: bool
    oneline_end: bool
    tag: int
    else_check: bool
    else_tag: int

@dataclass
class WriteCommand(StackElem):
    pass
