import re

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union, Callable


class ASTNode:
    pass


class String(ASTNode):
    def __init__(self,
                 value: str):
        self.value = value


    def __repr__(self):
        return f'String("{self.value}")'


class List(ASTNode):
    def __init__(self,
                 items: List[ASTNode]):
        self.items = items


    def __repr__(self):
        return f'List({self.items})'


class Variable(ASTNode):
    def __init__(self,
                 name: str):
        self.name = name


    def __repr__(self):
        return f'Variable("{self.name}")'


class RuleCall(ASTNode):
    def __init__(self,
                 name: str,
                 args: Dict[str, ASTNode]):
        self.name = name
        self.args = args


    def __repr__(self):
        return f'RuleCall("{self.name}", {self.args})'


class Target(ASTNode):
    def __init__(self,
                 props: Dict[str, Any]):
        self.props = props


    def __repr__(self):
        return f'Target({self.props})'
