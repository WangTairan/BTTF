from __future__ import annotations

import ast
import unittest

from readability_data.java_degradation.interferences.data_flow import (
    IntroduceNumericIntermediates as JavaNumericIntermediates,
)
from readability_data.java_degradation.interferences.expressions.literals import (
    EncodeIntegerLiterals as JavaHexIntegers,
)
from readability_data.java_degradation.registry import INTERFERENCE_CATALOG
from readability_data.python_degradation.core import Context
from readability_data.python_degradation.interferences.code_injection.common import (
    callable_insertion_points,
)
from readability_data.python_degradation.interferences.code_injection.low_readability_templates import (
    LOW_READABILITY_TEMPLATES,
)
from readability_data.python_degradation.interferences.code_injection.readable_templates import (
    READABLE_TEMPLATES,
)
from readability_data.python_degradation.interferences.data_flow import (
    IntroduceNumericIntermediates as PythonNumericIntermediates,
)
from readability_data.python_degradation.interferences.expressions.literals import (
    EncodeIntegerLiterals as PythonHexIntegers,
)
from readability_data.python_degradation.registry import INTERFERENCES
from readability_data.shared.alignment import (
    INTERFERENCE_SPECS,
    LOW_READABILITY_CODE_TEMPLATE_FAMILIES,
    READABLE_CODE_TEMPLATE_FAMILIES,
)


class CrossLanguageAlignmentTests(unittest.TestCase):
    def test_catalog_order_and_categories_are_identical(self) -> None:
        expected = [(item.category, item.slug) for item in INTERFERENCE_SPECS]
        self.assertEqual(
            [(item.category, item.slug) for item in INTERFERENCE_CATALOG], expected
        )
        self.assertEqual(
            [(item.category, item.slug) for item in INTERFERENCES.values()], expected
        )

    def test_hexadecimal_integer_policy_is_aligned(self) -> None:
        java = JavaHexIntegers().apply(
            b"class Example { int value() { return 137; } }", Context(1, "hex")
        )
        python = PythonHexIntegers().apply(
            "class Example:\n    def value(self):\n        return 137\n",
            Context(1, "hex"),
        )
        self.assertIn(b"return 0x89", java.content)
        self.assertIn("return 0x89", python.content)

    def test_numeric_intermediate_policy_is_aligned(self) -> None:
        java = JavaNumericIntermediates().apply(
            b"class Example { int value() { return 137; } }", Context(1, "split")
        )
        python = PythonNumericIntermediates().apply(
            "class Example:\n    def value(self):\n        return 137\n",
            Context(1, "split"),
        )
        self.assertEqual(java.stats["integer_literals_split"], 1)
        self.assertEqual(python.stats["integer_literals_split"], 1)
        self.assertIn(b"(a + b)", java.content)
        self.assertIn("(a + b)", python.content)
        ast.parse(python.content)

    def test_python_numeric_intermediates_preserve_elif_chain_syntax(self) -> None:
        source = """class Example:
    def value(self, item):
        if item == 2:
            return 3
        elif item == 4:
            return 5
        return 6
"""
        result = PythonNumericIntermediates().apply(source, Context(1, "elif"))
        self.assertEqual(result.stats["integer_literals_split"], 5)
        ast.parse(result.content)

    def test_code_template_cardinality_and_python_syntax(self) -> None:
        self.assertEqual(len(READABLE_TEMPLATES), len(READABLE_CODE_TEMPLATE_FAMILIES))
        self.assertEqual(
            len(LOW_READABILITY_TEMPLATES),
            len(LOW_READABILITY_CODE_TEMPLATE_FAMILIES),
        )
        for template in READABLE_TEMPLATES:
            lines = template(lambda role: role)
            ast.parse("def generated():\n" + "".join(f"    {x}\n" for x in lines))
        for template in LOW_READABILITY_TEMPLATES:
            lines = template(lambda role: role, 0x5A17)
            ast.parse("def generated():\n" + "".join(f"    {x}\n" for x in lines))

    def test_injection_target_cardinality_matches_contract(self) -> None:
        source = """class Example:
    def first(self):
        return 1

    def second(self):
        def nested():
            return 2
        return nested()
"""
        context = Context(9, "callables")
        callable_count = len(callable_insertion_points(source))
        dead = INTERFERENCES["insert-dead-branches"].apply(source, context)
        readable = INTERFERENCES["inject-readable-unrelated-code"].apply(
            source, context
        )
        opaque = INTERFERENCES["inject-low-readability-unrelated-code"].apply(
            source, context
        )
        self.assertEqual(dead.stats["dead_branches_inserted"], callable_count)
        self.assertEqual(readable.stats["readable_blocks_injected"], 1)
        self.assertEqual(opaque.stats["low_readability_blocks_injected"], 1)


if __name__ == "__main__":
    unittest.main()
