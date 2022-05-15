import unittest

from inspect import getmembers, isfunction
from functools import partial

import pronotepy
from pronotepy import ent


class TestENT(unittest.TestCase):
    functions: list

    @classmethod
    def setUpClass(cls) -> None:
        cls.functions = getmembers(
            ent, lambda x: isfunction(x) or isinstance(x, partial)
        )

    def test_functions(self) -> None:
        for func in self.functions:
            self.assertRaises(pronotepy.ENTLoginError, func[1], "username", "password")


if __name__ == "__main__":
    unittest.main()
