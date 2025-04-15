import os
import sys

from bootstrap.builder import Builder


def _build(cmd,
           builder):
    if len(cmd) <= 2:
        dag = builder.build_dependency_graph()
        build_order = dag.topological_sort()

        for target_name in build_order:
            builder.build_target(target_name)

        return

    target_name = cmd[2]
    builder.build_target(target_name)


def build(cmd):
    builder = Builder(".",
                      debug = True)

    _build(cmd,
           builder)


def build_release(cmd):
    builder = Builder(".",
                      debug = False)

    _build(cmd,
           builder)


def graph(cmd):
    builder = Builder(".",
                      debug = True)

    os.makedirs("build",
                exist_ok = True)

    dag = builder.build_dependency_graph()
    dag.visualize("build/dependency_graph")

    print("[!] dependency graph rendered to build/dependency_graph.pdf")


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("USAGE:\n  %s command\nWHERE" % sys.argv[0])
        print("  command\t\t`build` or `graph`")

        sys.exit(1)

    {
        "build": build,
        "build-release": build_release,
        "graph": graph,
    }[sys.argv[1]](sys.argv)

    sys.exit(0)
