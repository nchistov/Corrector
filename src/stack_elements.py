from dataclasses import dataclass

@dataclass
class Procedure:
    name: str
    tag: int

@dataclass
class If:
    no: bool
    symbol_check: bool
    check: int
    multiline: bool
    tag: int
    else_check: bool
    else_tag: int

@dataclass
class WriteCommand:
    pass
