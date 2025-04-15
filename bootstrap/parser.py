import re

from enum import Enum, auto
from dataclasses import dataclass

from .lexer import Lexer, Token, TokenType
from .ast import String, List, Variable, RuleCall, Target


class Parser:
    def __init__(self,
                 tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0]


    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]

        return self.current_token


    def eat(self,
            token_type):
        if self.current_token.type == token_type:
            token = self.current_token
            self.advance()

            return token

        line, col = self.current_token.line, self.current_token.col
        raise Exception(f"expected {token_type}, got {self.current_token.type} at line {line}, column {col}")


    def parse(self):
        node = self.expr()
        self.eat(TokenType.EOF)

        return node


    def expr(self):
        token = self.current_token

        if token.type == TokenType.STRING:
            self.advance()
            return String(token.value)

        elif token.type == TokenType.LBRACKET:
            return self.list()

        elif token.type == TokenType.IDENTIFIER:
            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == TokenType.LPAREN:
                return self.rule_call()

            self.advance()
            return Variable(token.value)

        else:
            line, col = token.line, token.col
            raise Exception(f"unexpected token: {token.type} at line {line}, column {col}")


    def list(self):
        self.eat(TokenType.LBRACKET)

        if self.current_token.type == TokenType.RBRACKET:
            self.advance()
            return List([])

        items = [self.expr()]

        while self.current_token.type == TokenType.COMMA:
            self.advance()
            items.append(self.expr())

        self.eat(TokenType.RBRACKET)

        return List(items)


    def rule_call(self):
        name = self.eat(TokenType.IDENTIFIER).value
        self.eat(TokenType.LPAREN)

        if self.current_token.type == TokenType.RPAREN:
            self.advance()
            return RuleCall(name, {})

        arg_name = self.eat(TokenType.IDENTIFIER).value
        self.eat(TokenType.EQUALS)

        args = {arg_name: self.expr()}

        while self.current_token.type == TokenType.COMMA:
            self.advance()

            arg_name = self.eat(TokenType.IDENTIFIER).value
            self.eat(TokenType.EQUALS)

            args[arg_name] = self.expr()

        self.eat(TokenType.RPAREN)

        return RuleCall(name, args)
