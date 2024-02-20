# Owner(s): ["module: dynamo"]
import functools

import torch
import torch._dynamo
import torch._dynamo.test_case
from torch._C._dynamo import guards

RootGuardManager = guards.RootGuardManager


def id_type(x):
    return id(type(x))


def equals_match(x, expected):
    return x == expected


def equals_match_verbose_code_parts(expected):
    return [f"x == {expected}"]


def ge_match(x, expected):
    return x >= expected


def ge_match_verbose_code_parts(expected):
    return f"expected >= {expected}"


def less_match(x, expected):
    return x < expected


def less_match_verbose_code_parts(expected):
    return [f"expected < {expected}"]


class GuardManagerTests(torch._dynamo.test_case.TestCase):
    def test_python_lambda_leaf_guard(self):
        const_guard = guards.LAMBDA_GUARD(
            functools.partial(equals_match, expected=5),
            equals_match_verbose_code_parts(5),
        )
        self.assertTrue(const_guard(5))
        self.assertFalse(const_guard(4))
        self.assertFalse(const_guard("foo"))

    def test_type_guard(self):
        foo = 4
        guard = guards.TYPE_MATCH(id_type(foo), ["type(x) == int"])

        self.assertTrue(guard(5))
        self.assertTrue(guard(4))
        self.assertFalse(guard("foo"))

        foo = {"a": 1}
        guard = guards.TYPE_MATCH(id_type(foo), ["type(x) == dict"])
        self.assertTrue(guard(foo))
        self.assertTrue(guard({}))
        self.assertFalse(guard(5))
        self.assertFalse(guard("foo"))

        class Foo:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        foo = Foo(1, 2)

        guard = guards.TYPE_MATCH(id_type(foo), ["type(x) == Foo"])
        self.assertTrue(guard(foo))
        self.assertFalse(guard({}))
        self.assertFalse(guard(5))
        self.assertFalse(guard("foo"))

    def test_id_guard(self):
        foo = 4
        guard = guards.ID_MATCH(id(foo), ["id(x) == id(foo)"])

        self.assertTrue(guard(foo))
        self.assertFalse(guard(5))
        self.assertFalse(guard("foo"))

        foo = {"a": 1}
        guard = guards.ID_MATCH(id(foo), ["id(x) == id(foo)"])
        self.assertTrue(guard(foo))
        self.assertFalse(guard({"a": 1}))
        self.assertFalse(guard({}))
        self.assertFalse(guard(5))

    def test_guard_manager_leaf_guard(self):
        guard_manager = RootGuardManager()
        guard_manager.add_type_match_guard(id_type(5), ["type(x) == int"])
        guard_manager.add_lambda_guard(
            functools.partial(ge_match, expected=5),
            ge_match_verbose_code_parts(expected=5),
        )
        guard_manager.add_lambda_guard(
            functools.partial(less_match, expected=10),
            less_match_verbose_code_parts(expected=10),
        )
        self.assertEqual(len(guard_manager.get_leaf_guards()), 3)
        self.assertEqual(len(guard_manager.get_accessors()), 0)
        self.assertTrue(guard_manager.check(6))
        self.assertFalse(guard_manager.check(4))
        self.assertFalse(guard_manager.check("foo"))


if __name__ == "__main__":
    from torch._dynamo.test_case import run_tests

    run_tests()
