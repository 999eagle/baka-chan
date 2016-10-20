# -*- coding: utf-8 -*-

from enum import Enum
import math

from errors import *

class Associativity(Enum):
	left = 0
	right = 1

class TokenType(Enum):
	invalid = 0
	number = 1
	variable = 2
	operator = 3

class Expression:
	def __init__(self, expr):
		self.expression = expr
		self.infix_tokens = []
		self.rpn_tokens = []

	@staticmethod
	def _split_operator_token(token):
		op = ''
		ops = []
		for char in token['token']:
			if 'a' <= char <= 'z':
				op += char
			else:
				if len(op) > 0:
					ops.append(op)
					op = ''
				elif len(ops) > 0 and ops[-1] == '*' and char == '*':
					ops = ops[:-1]
					char = '^'
				ops.append(char)
		if len(op) > 0:
			ops.append(op)
		return [{'type': TokenType.operator, 'token': o} for o in ops]

	def tokenize(self):
		expression = self.expression.lower()
		tokens = []
		token = {'token': '', 'type': TokenType.invalid}
		for char in expression:
			if char == '$':
				# positional variable starts with $
				token = {'token': '', 'type': TokenType.variable}
				tokens.append(token)
			elif char == ' ':
				# space ends current token and start an invalid one
				token = {'token': '', 'type': TokenType.invalid}
			elif '0' <= char <= '9':
				# number or variable can contain digits
				if token['type'] in (TokenType.number, TokenType.variable):
					token['token'] += char
				else:
					token = {'token': char, 'type': TokenType.number}
					tokens.append(token)
			elif char == '.':
				# either append to number or start new number
				if token['type'] == TokenType.number:
					token['token'] += char
				else:
					token = {'token': '0.', 'type': TokenType.number}
					tokens.append(token)
			else:
				# everything else is an operator
				if token['type'] == TokenType.operator:
					token['token'] += char
				else:
					token = {'token': char, 'type': TokenType.operator}
					tokens.append(token)

		# first post-proc pass: split tokens
		i = 0
		while i < len(tokens):
			token = tokens[i]
			t = token['token']
			if token['type'] == TokenType.operator:
				split_tokens = self._split_operator_token(token)
				tokens = tokens[:i] + split_tokens + tokens[i + 1:]
				i += len(split_tokens) - 1
			elif token['type'] == TokenType.number:
				if t.count('.') > 1:
					split = t.split('.')
					split_tokens = [{'type': TokenType.number, 'token': split[0] + '.' + split[1]}]
					for s in split[2:]:
						split_tokens.append({'type': TokenType.number, 'token': '0.' + s})
					tokens = tokens[:i] + split_tokens + tokens[i + 1:]
					i += len(split_tokens) - 1
			i += 1
		# second post-proc pass: parse numbers, variables
		for token in tokens:
			t = token['token']
			if token['type'] == TokenType.operator and t in Expression._operators and Expression._operators[t]['arity'] == 0:
				token['type'] = TokenType.number
				token['value'] = Expression._operators[t]['value']
			elif token['type'] == TokenType.number:
				token['value'] = float(t)
			elif token['type'] == TokenType.variable:
				token['value'] = int(t)

		self.infix_tokens = tokens

	def to_rpn(self):
		rpn_tokens = []
		stack = []
		if len(self.infix_tokens) == 0:
			self.tokenize()

		for token in self.infix_tokens:
			if token['type'] in (TokenType.number, TokenType.variable):
				rpn_tokens.append(token)
				continue
			if token['type'] == TokenType.operator:
				if token['token'] == '(':
					stack.append(token)
				elif token['token'] == ')':
					while True:
						t = stack.pop()
						if t['token'] == '(':
							break
						rpn_tokens.append(t)
					if len(stack) > 0:
						t = stack[-1]
						if t['token'] in Expression._operators and 'precedence' not in Expression._operators[t['token']] and Expression._operators[t['token']]['arity'] > 0:
							stack.pop()
							rpn_tokens.append(t)
				elif token['token'] == ',':
					while True:
						t = stack.pop()
						if t['token'] == '(':
							break
						rpn_tokens.append(t)
				else:
					if token['token'] in Expression._operators:
						# token is known operator
						o = Expression._operators[token['token']]
						if 'precedence' not in o:
							stack.append(token)
						else:
							while len(stack) > 0:
								t = stack[-1]
								if t['token'] not in Expression._operators:
									break
								o2 = Expression._operators[t['token']]
								prec = o['precedence'] + (0 if o.get('associativity', Associativity.left) == Associativity.left else 1)
								if prec <= o2.get('precedence', -1):
									stack.pop()
									rpn_tokens.append(t)
								else:
									break
							stack.append(token)
					else:
						# token is unknown "operator" i.e. text --> named variable
						rpn_tokens.append({'type': TokenType.variable, 'token': token['token']})
		while len(stack) > 0:
			rpn_tokens.append(stack.pop())
		self.rpn_tokens = rpn_tokens

	def eval(self, *pos_vars, **named_vars):
		if len(self.rpn_tokens) == 0:
			self.to_rpn()
		stack = []
		for token in self.rpn_tokens:
			if token['type'] == TokenType.number:
				stack.append(token['value'])
			elif token['type'] == TokenType.variable:
				if 'value' in token:
					index = token['value']
					if len(pos_vars) <= index:
						raise VariableOutOfRangeException('Variable with index {0} not given.'.format(index))
					stack.append(pos_vars[index])
				else:
					name = token['token']
					if name not in named_vars:
						raise VariableOutOfRangeException('Variable with name {0} not given.'.format(name))
					stack.append(named_vars[name])
			elif token['type'] == TokenType.operator:
				o = Expression._operators[token['token']]
				arity = o['arity']
				if len(stack) < arity:
					raise MalformedExpressionException('Expected {0} arguments for operator {1}. Got {2}.'.format(arity, token['token'], len(stack)))
				args = stack[-arity:]
				stack = stack[:-arity]
				stack.append(Expression._calc[token['token']](*args))
		if len(stack) != 1:
			raise MalformedExpressionException('Malformed expression.')
		return stack.pop()

	_operators = {
		# binary operators
		'+': {'arity': 2, 'precedence': 1, 'associativity': Associativity.left},
		'-': {'arity': 2, 'precedence': 1, 'associativity': Associativity.left},
		'*': {'arity': 2, 'precedence': 2, 'associativity': Associativity.left},
		'/': {'arity': 2, 'precedence': 2, 'associativity': Associativity.left},
		'^': {'arity': 2, 'precedence': 3, 'associativity': Associativity.right},
		# unary operators
		'°': {'arity': 1, 'precedence': 4, 'associativity': Associativity.left},
		# binary functions
		'max': {'arity': 2},
		'min': {'arity': 2},
		# unary functions
		'exp': {'arity': 1},
		'sin': {'arity': 1},
		'cos': {'arity': 1},
		'ln': {'arity': 1},
		'sqrt': {'arity': 1},
		'tan': {'arity': 1},
		'abs': {'arity': 1},
		'asin': {'arity': 1},
		'acos': {'arity': 1},
		'atan': {'arity': 1},
		'deg': {'arity': 1},
		# constants
		'tau': {'arity': 0, 'value': 6.2831853071795864769252867 },
		'e': {'arity': 0, 'value': 2.7182818284590452353602874 },
	}

	_calc = {
		'+': (lambda a, b: a + b),
		'-': (lambda a, b: a - b),
		'*': (lambda a, b: a * b),
		'/': (lambda a, b: a / b),
		'^': (lambda a, b: a ** b),
		'°': (lambda a: a / 360 * 6.2831853071795864769252867),
		'max': max,
		'min': min,
		'exp': math.exp,
		'sin': math.sin,
		'cos': math.cos,
		'ln': math.log,
		'sqrt': math.sqrt,
		'tan': math.tan,
		'abs': math.fabs,
		'asin': math.asin,
		'acos': math.acos,
		'atan': math.atan,
		'deg': math.degrees,
	}
