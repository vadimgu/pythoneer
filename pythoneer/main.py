import argparse
import sys
from typing import TextIO, Optional, List

import astor

from pythoneer.programmer import Programmer


parser = argparse.ArgumentParser()
parser.add_argument("filename")
parser.add_argument("name")
parser.add_argument(
    "--all", action="store_true", help="Display all generated functions"
)
parser.add_argument(
    "-w", "--working", action="store_true", help="Display all working functions."
)
# TODO
# parser.add_argument(
#     "-s",
#     "--show-test-results",
#     action="store_true",
#     help="Show test output for debugging.",
# )

# TODO:
# -i --interactive  interactive search
# -s --show-test-results

# TOOD:
# parser.add_argument("-i", "--inplace", action="store_false")

# TODO:
# parser.add_argument("-o", "--output", default=sys.stdout)


# TODO:
# parser.add_argument("--sample", type=int, help="Display n generated functions randomly sampled")


def main(stdout: TextIO, stderr: TextIO, args: Optional[List[str]] = None) -> None:
    if args is None:
        args = sys.argv[1:]
    options = parser.parse_args(args)

    with open(options.filename, "r") as fd:
        programmer = Programmer.from_stream(fd, options.filename, options.name)

        if options.all:
            for f in programmer:
                print(astor.to_source(f), end="\n-----------------\n", file=stdout)
        elif options.working:
            for f in programmer.filter():
                print(astor.to_source(f), end="\n-----------------\n", file=stdout)
        else:
            f = programmer.first()
            print(astor.to_source(f))
