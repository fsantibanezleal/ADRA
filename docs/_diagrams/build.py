"""Render all doc figures to ../images/*.svg.  Run:  python build.py"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import figures  # noqa: E402

OUT = os.path.normpath(os.path.join(HERE, "..", "images"))


def main():
    os.makedirs(OUT, exist_ok=True)
    for name in figures.FIGURES:
        path = os.path.join(OUT, name + ".svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(figures.render(name))
        print("wrote", os.path.relpath(path, HERE))
    print(f"\n{len(figures.FIGURES)} figures -> {OUT}")


if __name__ == "__main__":
    main()
