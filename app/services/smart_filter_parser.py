"""
Smart Filter DSL Parser and SQLAlchemy Translator.

Parses a simple SQL-like DSL and translates it to SQLAlchemy filter conditions.
The DSL is never executed as raw SQL — it is parsed into an AST and translated
to safe ORM expressions.

Grammar:
    expression  = condition (("AND" | "OR") condition)*
    condition   = field_condition | relation_condition
    field_cond  = FIELD "IS" "NULL"
                | FIELD "IS" "NOT" "NULL"
                | FIELD "CONTAINS" STRING
                | FIELD ("=" | "!=" | ">" | "<" | ">=" | "<=") (STRING | NUMBER)
    rel_cond    = RELATION "COUNT" ("=" | "!=" | ">" | "<" | ">=" | "<=") NUMBER

Example:
    "firmierung IS NULL AND kontakte COUNT = 0"
"""
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import and_, or_, func, select


# ── Token Types ──────────────────────────────────────────────────────────

TOKEN_PATTERN = re.compile(
    r"""
    (?P<STRING>"[^"]*")          |  # Quoted string
    (?P<NUMBER>\d+)              |  # Integer
    (?P<GTE>>=)                  |  # Must come before GT
    (?P<LTE><=)                  |  # Must come before LT
    (?P<NEQ>!=)                  |  # Not equal
    (?P<EQ>=)                    |  # Equal
    (?P<GT>>)                    |  # Greater than
    (?P<LT><)                    |  # Less than
    (?P<WORD>[a-z_][a-z0-9_]*)  |  # Identifier or keyword
    (?P<SKIP>\s+)                |  # Whitespace (skip)
    (?P<ERROR>.)                    # Anything else is an error
    """,
    re.VERBOSE | re.IGNORECASE,
)

KEYWORDS = {"AND", "OR", "IS", "NOT", "NULL", "CONTAINS", "COUNT"}
COMPARISON_OPS = {"=", "!=", ">", "<", ">=", "<="}


@dataclass
class Token:
    type: str   # FIELD, RELATION, STRING, NUMBER, AND, OR, IS, NOT, NULL, CONTAINS, COUNT, EQ, NEQ, GT, LT, GTE, LTE
    value: str
    pos: int


class SmartFilterError(Exception):
    """Raised when DSL parsing or translation fails."""
    pass


# ── Tokenizer ────────────────────────────────────────────────────────────

def tokenize(dsl: str, field_names: set, relation_names: set) -> list[Token]:
    """Tokenize a DSL expression into a list of tokens."""
    tokens = []
    for match in TOKEN_PATTERN.finditer(dsl):
        kind = match.lastgroup
        value = match.group()
        pos = match.start()

        if kind == "SKIP":
            continue
        if kind == "ERROR":
            raise SmartFilterError(f"Unexpected character '{value}' at position {pos}")

        if kind == "STRING":
            tokens.append(Token("STRING", value.strip('"'), pos))
        elif kind == "NUMBER":
            tokens.append(Token("NUMBER", value, pos))
        elif kind in COMPARISON_OPS or kind in ("EQ", "NEQ", "GT", "LT", "GTE", "LTE"):
            tokens.append(Token(kind, value, pos))
        elif kind == "WORD":
            upper = value.upper()
            if upper in KEYWORDS:
                tokens.append(Token(upper, value, pos))
            elif value.lower() in field_names:
                tokens.append(Token("FIELD", value.lower(), pos))
            elif value.lower() in relation_names:
                tokens.append(Token("RELATION", value.lower(), pos))
            else:
                raise SmartFilterError(
                    f"Unknown field '{value}' at position {pos}. "
                    f"Allowed fields: {', '.join(sorted(field_names | relation_names))}"
                )

    return tokens


# ── Parser (Recursive Descent) ───────────────────────────────────────────

class Parser:
    """Parses token list into an AST (nested dicts)."""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token | None:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def advance(self) -> Token:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def expect(self, token_type: str) -> Token:
        token = self.peek()
        if not token or token.type != token_type:
            expected = token_type
            got = token.type if token else "end of input"
            pos = token.pos if token else len(str(self.tokens))
            raise SmartFilterError(f"Expected {expected}, got {got} at position {pos}")
        return self.advance()

    def parse(self) -> dict:
        """Parse the full expression."""
        if not self.tokens:
            raise SmartFilterError("Empty filter expression")
        result = self.parse_expression()
        if self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            raise SmartFilterError(f"Unexpected token '{token.value}' at position {token.pos}")
        return result

    def parse_expression(self) -> dict:
        """Parse: condition (("AND" | "OR") condition)*"""
        left = self.parse_condition()

        while self.peek() and self.peek().type in ("AND", "OR"):
            op = self.advance().type.lower()  # "and" or "or"
            right = self.parse_condition()

            # Flatten consecutive same-type operators: A AND B AND C → {"and": [A, B, C]}
            if isinstance(left, dict) and op in left:
                left[op].append(right)
            else:
                left = {op: [left, right]}

        return left

    def parse_condition(self) -> dict:
        """Parse a single condition (field or relation)."""
        token = self.peek()
        if not token:
            raise SmartFilterError("Unexpected end of expression")

        if token.type == "FIELD":
            return self.parse_field_condition()
        elif token.type == "RELATION":
            return self.parse_relation_condition()
        else:
            raise SmartFilterError(
                f"Expected field or relation name, got '{token.value}' at position {token.pos}"
            )

    def parse_field_condition(self) -> dict:
        """Parse: FIELD operator value"""
        field_token = self.advance()
        field_name = field_token.value

        next_token = self.peek()
        if not next_token:
            raise SmartFilterError(f"Expected operator after '{field_name}'")

        # IS NULL / IS NOT NULL
        if next_token.type == "IS":
            self.advance()
            not_token = self.peek()
            if not_token and not_token.type == "NOT":
                self.advance()
                self.expect("NULL")
                return {"field": field_name, "op": "is_not_null"}
            else:
                self.expect("NULL")
                return {"field": field_name, "op": "is_null"}

        # CONTAINS "text"
        if next_token.type == "CONTAINS":
            self.advance()
            value_token = self.expect("STRING")
            return {"field": field_name, "op": "contains", "value": value_token.value}

        # Comparison operators: =, !=, >, <, >=, <=
        if next_token.type in ("EQ", "NEQ", "GT", "LT", "GTE", "LTE"):
            op_token = self.advance()
            value_token = self.peek()
            if not value_token or value_token.type not in ("STRING", "NUMBER"):
                raise SmartFilterError(
                    f"Expected value after '{op_token.value}' at position {op_token.pos}"
                )
            self.advance()
            value = int(value_token.value) if value_token.type == "NUMBER" else value_token.value
            op_map = {"EQ": "eq", "NEQ": "neq", "GT": "gt", "LT": "lt", "GTE": "gte", "LTE": "lte"}
            return {"field": field_name, "op": op_map[op_token.type], "value": value}

        raise SmartFilterError(
            f"Expected operator (IS, CONTAINS, =, !=, etc.) after '{field_name}', "
            f"got '{next_token.value}' at position {next_token.pos}"
        )

    def parse_relation_condition(self) -> dict:
        """Parse: RELATION COUNT operator NUMBER"""
        rel_token = self.advance()
        rel_name = rel_token.value

        self.expect("COUNT")

        op_token = self.peek()
        if not op_token or op_token.type not in ("EQ", "NEQ", "GT", "LT", "GTE", "LTE"):
            raise SmartFilterError(
                f"Expected comparison operator after 'COUNT', "
                f"got '{op_token.value if op_token else 'end of input'}'"
            )
        self.advance()

        num_token = self.expect("NUMBER")

        op_map = {"EQ": "eq", "NEQ": "neq", "GT": "gt", "LT": "lt", "GTE": "gte", "LTE": "lte"}
        return {
            "relation": rel_name,
            "op": f"count_{op_map[op_token.type]}",
            "value": int(num_token.value),
        }


# ── Translator (AST → SQLAlchemy) ────────────────────────────────────────

class Translator:
    """Translates parsed AST to SQLAlchemy filter conditions."""

    def __init__(self, model, field_map: dict, relation_map: dict):
        """
        Args:
            model: The SQLAlchemy model class (e.g. ComUnternehmen)
            field_map: Dict mapping DSL field names to model columns
            relation_map: Dict mapping DSL relation names to model relationships
        """
        self.model = model
        self.field_map = field_map
        self.relation_map = relation_map

    def translate(self, ast: dict) -> Any:
        """Translate AST node to SQLAlchemy expression."""
        if "and" in ast:
            return and_(*[self.translate(node) for node in ast["and"]])
        if "or" in ast:
            return or_(*[self.translate(node) for node in ast["or"]])
        if "field" in ast:
            return self._translate_field(ast)
        if "relation" in ast:
            return self._translate_relation(ast)

        raise SmartFilterError(f"Unknown AST node: {ast}")

    def _translate_field(self, node: dict) -> Any:
        """Translate field condition to SQLAlchemy expression."""
        field_name = node["field"]
        op = node["op"]
        column = self.field_map[field_name]

        if op == "is_null":
            return column == None  # noqa: E711 — SQLAlchemy requires == None
        if op == "is_not_null":
            return column != None  # noqa: E711
        if op == "contains":
            return column.ilike(f"%{node['value']}%")
        if op == "eq":
            return column == node["value"]
        if op == "neq":
            return column != node["value"]
        if op == "gt":
            return column > node["value"]
        if op == "lt":
            return column < node["value"]
        if op == "gte":
            return column >= node["value"]
        if op == "lte":
            return column <= node["value"]

        raise SmartFilterError(f"Unknown field operator: {op}")

    def _translate_relation(self, node: dict) -> Any:
        """Translate relation COUNT condition to SQLAlchemy expression."""
        rel_name = node["relation"]
        op = node["op"]
        value = node["value"]
        relationship = self.relation_map[rel_name]

        # Optimized paths for COUNT = 0 and COUNT > 0
        if op == "count_eq" and value == 0:
            return ~relationship.any()
        if op == "count_gt" and value == 0:
            return relationship.any()
        if op == "count_eq" and value > 0:
            # COUNT = N requires subquery
            return self._count_subquery(rel_name, "eq", value)
        if op == "count_neq":
            return self._count_subquery(rel_name, "neq", value)
        if op == "count_gt":
            return self._count_subquery(rel_name, "gt", value)
        if op == "count_lt":
            if value == 1:
                return ~relationship.any()
            return self._count_subquery(rel_name, "lt", value)
        if op == "count_gte":
            if value == 1:
                return relationship.any()
            return self._count_subquery(rel_name, "gte", value)
        if op == "count_lte":
            return self._count_subquery(rel_name, "lte", value)

        raise SmartFilterError(f"Unknown relation operator: {op}")

    def _count_subquery(self, rel_name: str, op: str, value: int) -> Any:
        """Build a subquery for COUNT comparisons with N > 0."""
        relationship_prop = self.relation_map[rel_name]
        # Get the related model and foreign key from the relationship
        related_model = relationship_prop.property.mapper.class_
        # Find the FK column pointing back to our model
        for col in relationship_prop.property.local_columns:
            local_col = col
            break
        for pair in relationship_prop.property.local_remote_pairs:
            remote_col = pair[1]
            break

        # Correlated subquery: SELECT COUNT(*) FROM related WHERE related.fk = model.pk
        count_sq = (
            select(func.count())
            .where(remote_col == local_col)
            .correlate(self.model)
            .scalar_subquery()
        )

        op_map = {
            "eq": lambda: count_sq == value,
            "neq": lambda: count_sq != value,
            "gt": lambda: count_sq > value,
            "lt": lambda: count_sq < value,
            "gte": lambda: count_sq >= value,
            "lte": lambda: count_sq <= value,
        }
        return op_map[op]()


# ── Public API ────────────────────────────────────────────────────────────

def parse_and_translate(
    dsl: str,
    model,
    field_map: dict,
    relation_map: dict,
) -> Any:
    """
    Parse a DSL expression and translate it to a SQLAlchemy filter condition.

    Args:
        dsl: The filter DSL string, e.g. "firmierung IS NULL AND kontakte COUNT = 0"
        model: SQLAlchemy model class
        field_map: Dict mapping DSL field names to model column attributes
        relation_map: Dict mapping DSL relation names to model relationship attributes

    Returns:
        SQLAlchemy filter condition (usable in query.where())

    Raises:
        SmartFilterError: If the DSL is invalid
    """
    field_names = set(field_map.keys())
    relation_names = set(relation_map.keys())

    tokens = tokenize(dsl, field_names, relation_names)
    parser = Parser(tokens)
    ast = parser.parse()
    translator = Translator(model, field_map, relation_map)
    return translator.translate(ast)


def validate_dsl(
    dsl: str,
    field_map: dict,
    relation_map: dict,
) -> dict:
    """
    Validate a DSL expression without translating it.

    Returns:
        {"valid": True} or {"valid": False, "error": "..."}
    """
    field_names = set(field_map.keys())
    relation_names = set(relation_map.keys())

    try:
        tokens = tokenize(dsl, field_names, relation_names)
        parser = Parser(tokens)
        parser.parse()
        return {"valid": True}
    except SmartFilterError as e:
        return {"valid": False, "error": str(e)}


# ── Unternehmen-specific configuration ────────────────────────────────────

def get_unternehmen_field_map():
    """Returns the field map for ComUnternehmen filters."""
    from app.models.com import ComUnternehmen
    return {
        "kurzname": ComUnternehmen.kurzname,
        "firmierung": ComUnternehmen.firmierung,
        "strasse": ComUnternehmen.strasse,
        "strasse_hausnr": ComUnternehmen.strasse_hausnr,
        "geo_ort_id": ComUnternehmen.geo_ort_id,
        "geloescht_am": ComUnternehmen.geloescht_am,
    }


def get_unternehmen_relation_map():
    """Returns the relation map for ComUnternehmen filters."""
    from app.models.com import ComUnternehmen
    return {
        "kontakte": ComUnternehmen.kontakte,
        "organisationen": ComUnternehmen.organisation_zuordnungen,
    }


def parse_unternehmen_filter(dsl: str) -> Any:
    """
    Convenience function: Parse a DSL for ComUnternehmen.

    Returns a SQLAlchemy filter condition.
    """
    from app.models.com import ComUnternehmen
    return parse_and_translate(
        dsl,
        model=ComUnternehmen,
        field_map=get_unternehmen_field_map(),
        relation_map=get_unternehmen_relation_map(),
    )
