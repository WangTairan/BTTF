from __future__ import annotations

import unittest

from src.methods.cognascore.member_access_features import member_access_features


class MemberAccessFeaturesTest(unittest.TestCase):
    def test_deep_call_chain(self) -> None:
        features = member_access_features(
            "return request.getUser().getProfile().getName();"
        )
        self.assertEqual(features["member_access_density"], 3.0)
        self.assertEqual(features["member_access_chain_depth_mean"], 3.0)

    def test_separates_frequency_from_depth(self) -> None:
        features = member_access_features("return a.x + b.y + c.z;")
        self.assertEqual(features["member_access_density"], 3.0)
        self.assertEqual(features["member_access_chain_depth_mean"], 1.0)

    def test_supports_common_language_neutral_access_operators(self) -> None:
        features = member_access_features(
            "left?.value + ns::Type + pointer->field + python.attr"
        )
        self.assertEqual(features["member_access_density"], 4.0)
        self.assertEqual(features["member_access_chain_depth_mean"], 1.0)

    def test_ignores_declarations_comments_strings_and_decimal_points(self) -> None:
        source = """import java.util.List;
package example.api;
#include <project/header.hpp>
double value = 3.14;
String text = \"fake.member\";
// ignored.member
return user.name;
"""
        features = member_access_features(source)
        self.assertAlmostEqual(features["member_access_density"], 1.0 / 7.0)
        self.assertEqual(features["member_access_chain_depth_mean"], 1.0)

    def test_counts_nested_argument_chains_separately(self) -> None:
        features = member_access_features("return service.send(user.profile.name).status;")
        self.assertEqual(features["member_access_density"], 4.0)
        self.assertEqual(features["member_access_chain_depth_mean"], 2.0)


if __name__ == "__main__":
    unittest.main()
