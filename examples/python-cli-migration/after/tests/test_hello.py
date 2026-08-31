import unittest

from src.hello import greeting


class GreetingTests(unittest.TestCase):
    def test_greeting(self) -> None:
        self.assertEqual(greeting("Codex"), "你好，Codex！")


if __name__ == "__main__":
    unittest.main()
