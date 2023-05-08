import unittest

from inspect import getmembers, isfunction
from functools import partial

import pronotepy
from pronotepy import ent
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestENT(unittest.TestCase):
    functions: list

    @classmethod
    def setUpClass(cls) -> None:
        cls.functions = getmembers(
            ent,
            lambda x: (isfunction(x) and x.__name__ != "pronote_hubeduconnect")
            or isinstance(x, partial),
        )

    def test_functions(self) -> None:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(func[1], "username", "password"): func[0]
                for func in self.functions
            }
            for func in as_completed(futures):
                with self.subTest(futures[func]):
                    self.assertRaises(
                        (pronotepy.ENTLoginError, requests.exceptions.ConnectionError),
                        func.result,
                    )


if __name__ == "__main__":
    logging.debug("Testing")
    unittest.main()
