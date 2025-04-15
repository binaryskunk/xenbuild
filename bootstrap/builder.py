import os

from .dag import DAG
from .lexer import Lexer, Token, TokenType
from .parser import Parser
from .evaluator import Evaluator, EvaluationContext
from .ast import ASTNode, String, List, Variable, RuleCall, Target


class Builder:
    def __init__(self,
                 repo_root,
                 debug = True):
        self.repo_root = os.path.abspath(repo_root)

        self.eval_ctx = EvaluationContext(self.repo_root,
                                          debug)
        self.evaluator = Evaluator(self.eval_ctx)


    def parse_build_file(self,
                         build_filepath):
        with open(build_filepath, "r") as fp:
            content = fp.read()

        rel_dir = os.path.dirname(os.path.relpath(build_filepath,
                                                  self.repo_root))
        self.eval_ctx.current_dir = rel_dir

        lexer = Lexer(content)
        tokens = lexer.tokenize()

        parser = Parser(tokens)

        nodes = []
        while parser.current_token.type != TokenType.EOF:
            nodes.append(parser.expr())

        return nodes


    def evaluate_build_file(self,
                            build_filepath):
        targets = []

        nodes = self.parse_build_file(build_filepath)
        for node in nodes:
            result = self.evaluator.evaluate(node)
            if isinstance(result, Target):
                targets.append(result)

        return targets


    def discover_build_files(self):
        build_files = []
        for root, _, files in os.walk(self.repo_root):
            for file in files:
                if file == "BUILD":
                    build_files.append(os.path.join(root, file))

        return build_files


    def build_dependency_graph(self):
        build_files = self.discover_build_files()
        for build_file in build_files:
            self.evaluate_build_file(build_file)

        graph = DAG()

        for target_name, target in self.eval_ctx.targets.items():
            graph.add_node(target_name, target)

        for target_name, target in self.eval_ctx.targets.items():
            for dep_name in target.props["deps"]:
                if dep_name not in self.eval_ctx.targets:
                    print(f"WARNING: target {target_name} depends on undefined target {dep_name}")
                    continue

                graph.add_edge(dep_name, target_name)

        return graph


    def build_target(self,
                     target_name):
        dag = self.build_dependency_graph()

        if target_name not in self.eval_ctx.targets:
            raise ValueError(f"unknown target: {target_name}")

        try:
            build_order = dag.topological_sort()
        except ValueError as err:
            print(f"error: {err}")
            return

        target_offset = build_order.index(target_name) + 1
        build_order = build_order[:target_offset]

        target_and_deps = set()
        self._collect_dependencies(dag,
                                   target_name,
                                   target_and_deps)

        filtered_build_order = [t for t in build_order
                                if t in target_and_deps]

        built_deps = []
        for t in filtered_build_order:
            self._build_single_target(self.eval_ctx.targets[t],
                                      built_deps)
            built_deps.append(self.eval_ctx.targets[t])


    def _collect_dependencies(self,
                              dag,
                              target_name,
                              result):
        result.add(target_name)
        for dep in dag.get_dependencies(target_name):
            if dep not in result:
                self._collect_dependencies(dag,
                                           dep,
                                           result)


    def _build_single_target(self,
                             target,
                             built_deps):
        if len(target.props["build"]) <= 0:
            return

        print(f"[+] building {target.props['name']} ...")

        os.makedirs(os.path.dirname(target.props["out"]),
                    exist_ok = True)
        for obj in target.props["obj"]:
            os.makedirs(os.path.dirname(obj),
                        exist_ok = True)

        args = ["-std=c++20",
                "-Wall",
                "-Wextra",
                "-Wno-unused-command-line-argument",
                "-L./build/lib"]
        for dep in built_deps:
            if dep.props["name"] not in target.props["deps"]:
                continue

            for inc_flag in dep.props["include_flags"]:
                args.append(inc_flag)

            for link_flag in dep.props["link_flags"]:
                args.append(link_flag)

        build_cmds = []
        for i in range(len(target.props["obj"])):
            in_file = target.props["in"][i]
            obj = target.props["obj"][i]

            cmd = target.props["build"]
            cmd = cmd.replace("@IN@", in_file)
            cmd = cmd.replace("@OBJ@", obj)
            cmd = cmd.replace("@ARGS@", ' '.join(args))

            build_cmds.append(cmd)

        link_cmd = target.props["link"]
        link_cmd = link_cmd.replace("@OBJ@",
                                    " ".join(target.props["obj"]))
        link_cmd = link_cmd.replace("@OUT@",
                                    target.props["out"])
        link_cmd = link_cmd.replace("@ARGS@", ' '.join(args))

        for build_cmd in build_cmds:
            print(f"\t~> executing: {build_cmd}")
            os.system(build_cmd)

        print(f"\t~> executing: {link_cmd}")
        os.system(link_cmd)

        print(f"\n[!] done building {target.props['name']}\n")
