import re
import subprocess as sp

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union, Callable

from .ast import ASTNode, String, List, Variable, RuleCall, Target


class EvaluationContext:
    def __init__(self,
                 repo_root,
                 debug = True):
        self.debug = debug

        self.variables = {}
        self.rules = {}
        self.targets = {}

        self.repo_root = repo_root
        self.current_dir = ""

        self.register_rule("glob", self.glob_rule)
        self.register_rule("cc_binary", self.cc_binary_rule)
        self.register_rule("cc_library", self.cc_library_rule)
        self.register_rule("system_cc_library", self.system_cc_library_rule)


    def register_rule(self,
                      name: str,
                      func: Callable):
        self.rules[name] = func


    def register_variable(self,
                          name: str,
                          value: Any):
        self.variables[name] = value


    def register_target(self,
                        target: Target):
        self.targets[target.props["name"]] = target


    def glob_rule(self,
                  args: Dict[str, Any]) -> List:
        pattern = args.get("pattern")
        if not pattern:
            raise ValueError("glob() requires a pattern")

        import glob as glob_module
        import os

        full_pattern = os.path.join(self.repo_root,
                                    self.current_dir,
                                    pattern)
        matching_files = glob_module.glob(full_pattern,
                                          recursive = True)

        prefix_len = len(os.path.join(self.repo_root,
                                      self.current_dir)) + 1
        relative_files = [f[prefix_len:]
                          for f in matching_files if os.path.isfile(f)]

        return List([String(f) for f in relative_files])


    def cc_binary_rule(self,
                       args: Dict[str, Any]) -> Target:
        name = args.get("name")
        if not name:
            raise ValueError("cc_binary() requires a name")

        sources = args.get("sources", [])
        includes = args.get("includes", [])
        deps = args.get("deps", [])

        full_sources = [f"./{self.current_dir}/{s}"
                        for s in sources]
        obj_files = [f"./build/obj/{self.current_dir}/{s.replace('.cc', '.o')}"
                     for s in sources]

        include_flags = [f"-I./{self.current_dir}/{inc}"
                         for inc in includes]

        debug_flags = "-g -O1 -DDEBUG" if self.debug else "-O2"

        props = {
            "name": f"@/{self.current_dir}/{name}",
            "include_flags": include_flags,
            "link_flags": [],
            "in": full_sources,
            "obj": obj_files,
            "out": f"build/bin/{name}",
            "build": f"c++ -c @IN@ -o @OBJ@ {''.join(include_flags)} @ARGS@ {debug_flags}",
            "link": f"c++ @OBJ@ -o @OUT@ {''.join(include_flags)} @ARGS@ {debug_flags}",
            "deps": deps
        }

        return Target(props)


    def cc_library_rule(self,
                        args: Dict[str, Any]):
        # TODO: remove duplicated code from cc_binary and cc_library rules

        name = args.get("name")
        if not name:
            raise ValueError("cc_library() requires a name")

        sources = args.get("sources", [])
        includes = args.get("includes", [])
        deps = args.get("deps", [])

        full_sources = [f"./{self.current_dir}/{s}"
                        for s in sources]
        obj_files = [f"./build/obj/{self.current_dir}/{s.replace('.cc', '.o')}"
                     for s in sources]

        include_flags = [f"-I./{self.current_dir}/{inc}"
                         for inc in includes]

        debug_flags = "-g -O1 -DDEBUG" if self.debug else "-O2"

        props = {
            "name": f"@/{self.current_dir}/{name}",
            "include_flags": include_flags,
            "link_flags": [f"-l{name}"],
            "in": full_sources,
            "obj": obj_files,
            "out": f"build/lib/lib{name}.a",
            "build": f"c++ -c @IN@ -o @OBJ@ {''.join(include_flags)} @ARGS@ {debug_flags}",
            "link": f"ar rcs @OUT@ @OBJ@",
            "deps": deps
        }

        return Target(props)


    def system_cc_library_rule(self,
                               args):
        name = args.get("name")
        if not name:
            raise ValueError("system_cc_library() requires a name")

        pkgconfig = args.get("pkgconfig", [])
        links, includes = self._pkgconfig_call(pkgconfig)
        links, includes = links.replace("\n", ""), includes.replace("\n", "")

        props = {
            "name": f"@/{self.current_dir}/{name}",
            "include_flags": [includes],
            "link_flags": [links],
            "in": [],
            "obj": [],
            "out": "",
            "build": "",
            "link": "",
            "deps": []
        }

        return Target(props)


    def _pkgconfig_call(self,
                        lib):
        includes = sp.check_output(["pkg-config", "--cflags", lib])
        links = sp.check_output(["pkg-config", "--libs", lib])

        return links.decode("utf-8"), includes.decode("utf-8")


class Evaluator:
    def __init__(self,
                 ctx: EvaluationContext):
        self.ctx = ctx


    def evaluate(self,
                 node: ASTNode) -> Any:
        if isinstance(node, String):
            return node.value

        elif isinstance(node, List):
            return [self.evaluate(item)
                    for item in node.items]

        elif isinstance(node, Variable):
            if node.name not in self.ctx.variables:
                raise ValueError(f"undefined variable: {node.name}")

            return self.evaluate(self.ctx.variables[node.name])

        elif isinstance(node, RuleCall):
            if node.name not in self.ctx.rules:
                raise ValueError(f"undefined rule: {node.name}")

            evaluated_args = {}
            for k, v in node.args.items():
                eval_result = self.evaluate(v)

                if isinstance(eval_result, List):
                    evaluated_args[k] = [self.evaluate(item)
                                         for item in eval_result.items]
                else:
                    evaluated_args[k] = eval_result

            result = self.ctx.rules[node.name](evaluated_args)

            if isinstance(result, Target):
                self.ctx.register_target(result)

            return result

        elif isinstance(node, Target):
            return node

        else:
            raise ValueError(f"unknown node type: {type(node)}")
