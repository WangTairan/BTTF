import contextlib
import io
import json
import unittest

from readability_data.cli import build_parser, main


class CliTest(unittest.TestCase):
    def test_removed_progressive_command_is_rejected(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                build_parser().parse_args(["java-degrade"])

    def test_separate_interference_options_are_parsed(self) -> None:
        args = build_parser().parse_args(
            [
                "interfere",
                "--input",
                "source",
                "--output",
                "constructed",
                "--interferences",
                "remove-comments",
                "mislead-identifiers",
            ]
        )
        self.assertEqual(
            args.interferences,
            ["remove-comments", "mislead-identifiers"],
        )

    def test_interference_registry_command_is_available(self) -> None:
        args = build_parser().parse_args(["list-interferences"])
        self.assertEqual(args.command, "list-interferences")

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main(["list-interferences"])
        rows = json.loads(output.getvalue())
        self.assertEqual(len(rows), 13)
        self.assertTrue(all("category" in row for row in rows))
        self.assertEqual(
            next(row for row in rows if row["interference"] == "mislead-identifiers")[
                "category"
            ],
            "identifiers",
        )

    def test_language_explicit_aliases_and_python_catalog(self) -> None:
        java_args = build_parser().parse_args(
            [
                "java-interfere",
                "--input",
                "source",
                "--output",
                "constructed",
            ]
        )
        self.assertEqual(java_args.command, "java-interfere")

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main(["list-python-interferences"])
        rows = json.loads(output.getvalue())
        self.assertEqual(len(rows), 13)
        self.assertEqual(
            {row["category"] for row in rows},
            {
                "comments",
                "identifiers",
                "expressions",
                "data-flow",
                "code-injection",
                "layout",
                "control-flow",
            },
        )


if __name__ == "__main__":
    unittest.main()
