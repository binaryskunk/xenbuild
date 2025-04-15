// Copyright 2025 Lavínia Rodrigues

#include <xenbuild/dep_graph.hh>

#include <fmt/core.h>

#include <algorithm>
#include <iterator>
#include <stdexcept>
#include <fstream>
#include <ranges>
#include <set>
#include <vector>
#include <unordered_map>
#include <string>

#include <sktd/common.hh>

// NOLINTBEGIN(whitespace/indent_namespace)

namespace xenbuild {

auto dependency_graph::_is_reachable(const std::string& start,
                                     const std::string& end) -> bool {
  std::set<std::string> visited;
  std::vector<std::string> queue = {start};

  while (queue.size() > 0) {
    auto current = queue.back();
    queue.pop_back();

    if (current == end) {
      return true;
    }
    if (visited.contains(current)) {
      continue;
    }

    visited.insert(current);

    std::copy(this->_edges[current].begin(), this->_edges[current].end(),
              std::back_inserter(queue));
  }

  return false;
}

auto dependency_graph::add_target(const std::string& target_name,
                                  build_target target) -> void {
  this->_nodes.insert_or_assign(target_name, target);

  this->_edges.try_emplace(target_name);
  this->_reverse_edges.try_emplace(target_name);
}

auto dependency_graph::map_dep(const std::string& from, const std::string& to)
    -> void {
  sktd::ensure(this->_nodes.contains(from),
               fmt::format("node {} does not exist", from));
  sktd::ensure(this->_nodes.contains(to),
               fmt::format("node {} does not exist", to));

  this->_edges[from].insert(to);
  this->_reverse_edges[to].insert(from);

  if (this->_is_reachable(to, from)) {
    this->_edges[from].erase(to);
    this->_reverse_edges[to].erase(from);

    throw std::runtime_error(
        fmt::format("adding edge {} -> {} would create a cycle", from, to));
  }
}

auto dependency_graph::get_dependencies(const std::string& target_name)
    -> std::set<std::string> {
  sktd::ensure(this->_nodes.contains(target_name),
               fmt::format("target {} does not exist", target_name));

  return this->_reverse_edges[target_name];
}

auto dependency_graph::get_dependents(const std::string& target_name)
    -> std::set<std::string> {
  sktd::ensure(this->_nodes.contains(target_name),
               fmt::format("target {} does not exist", target_name));

  return this->_edges[target_name];
}

auto dependency_graph::get_target(const std::string& target_name)
    -> build_target {
  sktd::ensure(this->_nodes.contains(target_name),
               fmt::format("target {} does not exist", target_name));

  return this->_nodes[target_name];
}

auto dependency_graph::sort() -> std::vector<std::string> {
  std::unordered_map<std::string, u64> in_degree;
  for (auto& [node, _] : this->_nodes) {
    in_degree.insert({node, this->_reverse_edges[node].size()});
  }

  std::vector<std::string> queue;
  auto zero_degree = [](auto pair) {
    auto& [_, degree] = pair;

    return degree == 0;
  };
  for (auto& [node, _] : in_degree | std::views::filter(zero_degree)) {
    queue.push_back(node);
  }

  std::vector<std::string> result;
  while (queue.size() > 0) {
    auto current = queue.back();
    queue.pop_back();

    for (const auto& dependent : this->_edges[current]) {
      in_degree[dependent] -= 1;

      if (in_degree[dependent] == 0) {
        queue.push_back(dependent);
      }
    }
  }

  sktd::ensure(
      result.size() == this->_nodes.size(),
      "dependency graph contains a cycle, cannot perform topological sort");

  return result;
}

auto dependency_graph::visualize(const std::string& filename) -> void {
  std::ofstream fp{filename};
  sktd::ensure(fp.is_open(), "failed to open graphviz file for writing");

  fp << "digraph {\n";

  for (const auto& [name, _] : this->_nodes) {
    fp << fmt::format("  \"{}\" [label=\"{}\"]\n", name, name);
  }

  for (const auto& [from, to_set] : this->_edges) {
    for (const auto& to : to_set) {
      fp << fmt::format("  \"{}\" -> \"{}\"\n", from, to);
    }
  }

  fp << "}";
  fp.close();
}

}  // namespace xenbuild

// NOLINTEND
