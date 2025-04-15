class DAG:
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.reverse_edges = {}


    def add_node(self,
                 node_id,
                 data = None):
        if node_id in self.nodes:
            self.nodes[node_id] = data
            return

        self.nodes[node_id] = data
        self.edges[node_id] = set()
        self.reverse_edges[node_id] = set()


    def add_edge(self,
                 from_node,
                 to_node):
        if from_node not in self.nodes:
            raise ValueError(f"Node {from_node} does not exist")
        if to_node not in self.nodes:
            raise ValueError(f"Node {to_node} does not exist")

        self.edges[from_node].add(to_node)
        self.reverse_edges[to_node].add(from_node)

        if self._creates_cycle(from_node, to_node):
            self.edges[from_node].remove(to_node)
            self.reverse_edges[to_node].remove(from_node)

            raise ValueError(f"Adding edge {from_node} -> {to_node} would create a cycle")


    def _creates_cycle(self,
                       from_node,
                       to_node):
        return self._is_reachable(to_node, from_node)


    def _is_reachable(self,
                      start,
                      end):
        visited = set()
        queue = [start]

        while queue:
            current = queue.pop(0)
            if current == end:
                return True
            if current in visited:
                continue

            visited.add(current)
            queue.extend(self.edges[current])

        return False


    def get_dependencies(self,
                         node_id):
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} does not exist")

        return self.reverse_edges[node_id]


    def get_dependents(self,
                       node_id):
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} does not exist")

        return self.edges[node_id]


    def get_node_data(self,
                      node_id):
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} does not exist")

        return self.nodes[node_id]


    def topological_sort(self):
        in_degree = {node: len(self.reverse_edges[node])
                     for node in self.nodes}
        queue = [node
                 for node, degree in in_degree.items()
                 if degree == 0]

        result = []
        while queue:
            current = queue.pop(0)
            result.append(current)

            for dependent in list(self.edges[current]):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(result) != len(self.nodes):
            raise ValueError("Dependency graph contains a cycle, cannot perform topological sort")

        return result


    def find_all_paths(self,
                       start,
                       end):
        paths = []

        def dfs(current,
                path,
                visited):
            if current == end:
                paths.append(path[:])
                return

            visited.add(current)
            for neighbor in self.edges[current]:
                if neighbor not in visited:
                    path.append(neighbor)
                    dfs(neighbor, path, visited.copy())

                    path.pop()

        dfs(start, [start], set())

        return paths


    def has_cycles(self):
        try:
            self.topological_sort()
            return False

        except ValueError:
            return True


    def visualize(self,
                  filename = "dag.png"):
        try:
            import graphviz
        except ImportError:
            print("graphviz package not found, install it with `pip install graphviz`")
            return

        dot = graphviz.Digraph(comment = "Build Dependency Graph")

        for node_id in self.nodes:
            dot.node(str(node_id), str(node_id))

        for from_node, to_nodes in self.edges.items():
            for to_node in to_nodes:
                dot.edge(str(from_node), str(to_node))

        dot.render(filename)
