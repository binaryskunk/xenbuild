import re

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union, Callable


class TokenType(Enum):
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    EQUALS = auto()
    COMMA = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int


class Lexer:
    def __init__(self,
                 text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.current_char = self.text[0] if text else None


    def advance(self):
        self.pos += 1
        if self.pos >= len(self.text):
            self.current_char = None
            return

        self.current_char = self.text[self.pos]
        if self.current_char == '\n':
            self.line += 1
            self.col = 1

            return

        self.col += 1


    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()


    def identifier(self):
        result = ''

        while self.current_char is not None and (self.current_char.isalnum() or self.current_char in '_:@/.-'):
            result += self.current_char
            self.advance()

        return result


    def string(self):
        result = ''

        self.advance()
        while self.current_char is not None and self.current_char != '"':
            if self.current_char == '\\':
                self.advance()
                if self.current_char == 'n':
                    result += '\n'
                elif self.current_char == 't':
                    result += '\t'
                else:
                    result += self.current_char
            else:
                result += self.current_char

            self.advance()

        self.advance()

        return result


    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isalpha() or self.current_char in '_@/':
                return Token(TokenType.IDENTIFIER, self.identifier(), self.line, self.col)

            if self.current_char == '"':
                return Token(TokenType.STRING, self.string(), self.line, self.col)

            if self.current_char == '=':
                token = Token(TokenType.EQUALS, '=', self.line, self.col)
                self.advance()

                return token

            if self.current_char == ',':
                token = Token(TokenType.COMMA, ',', self.line, self.col)
                self.advance()

                return token

            if self.current_char == '(':
                token = Token(TokenType.LPAREN, '(', self.line, self.col)
                self.advance()

                return token

            if self.current_char == ')':
                token = Token(TokenType.RPAREN, ')', self.line, self.col)
                self.advance()

                return token

            if self.current_char == '[':
                token = Token(TokenType.LBRACKET, '[', self.line, self.col)
                self.advance()

                return token

            if self.current_char == ']':
                token = Token(TokenType.RBRACKET, ']', self.line, self.col)
                self.advance()

                return token

            raise Exception(f"invalid character: {self.current_char} at line {self.line}, column {self.col}")

        return Token(TokenType.EOF, '', self.line, self.col)


    def tokenize(self):
        tokens = []

        token = self.get_next_token()
        while token.type != TokenType.EOF:
            tokens.append(token)
            token = self.get_next_token()

        tokens.append(token)

        return tokens
