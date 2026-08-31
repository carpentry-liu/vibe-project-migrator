from __future__ import annotations

import sys


def greeting(name: str) -> str:
    return f"你好，{name}！"


def main(argv: list[str] | None = None) -> int:
    arguments = argv if argv is not None else sys.argv[1:]
    print(greeting(arguments[0] if arguments else "世界"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
