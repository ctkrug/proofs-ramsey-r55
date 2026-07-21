#include <array>
#include <bit>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

constexpr int N = 43;
constexpr int EDGE_COUNT = N * (N - 1) / 2;
constexpr std::uint64_t VERTEX_MASK = (std::uint64_t{1} << N) - 1;
constexpr const char* TITLE =
    "# Supplementary Data 4: The coloring matrix with only 2 monochromatic 5-cliques of a complete graph with 43 nodes";

using Rows = std::array<std::uint64_t, N>;

struct Parsed {
  Rows rows{};
  int edge_count = 0;
};

[[noreturn]] void fail(const std::string& message) {
  throw std::runtime_error(message);
}

Parsed parse_matrix(const std::string& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) fail("cannot open matrix");
  std::string line;
  if (!std::getline(input, line) || line != TITLE) fail("title mismatch");

  std::array<std::array<int, N>, N> matrix{};
  for (int row = 0; row < N; ++row) {
    if (!std::getline(input, line)) fail("missing matrix row");
    std::istringstream tokens(line);
    for (int column = 0; column < N; ++column) {
      std::string token;
      if (!(tokens >> token) || (token != "0" && token != "1")) {
        fail("row contains a missing or nonbinary token");
      }
      matrix[row][column] = token[0] - '0';
    }
    std::string extra;
    if (tokens >> extra) fail("row contains extra tokens");
  }
  if (std::getline(input, line)) fail("extra line after matrix");

  Parsed parsed;
  for (int u = 0; u < N; ++u) {
    if (matrix[u][u] != 0) fail("nonzero diagonal");
    for (int v = u + 1; v < N; ++v) {
      if (matrix[u][v] != matrix[v][u]) fail("asymmetric matrix");
      if (matrix[u][v]) {
        parsed.rows[u] |= std::uint64_t{1} << v;
        parsed.rows[v] |= std::uint64_t{1} << u;
        ++parsed.edge_count;
      }
    }
  }
  return parsed;
}

std::uint64_t greater_than(int vertex) {
  if (vertex >= N - 1) return 0;
  return VERTEX_MASK & ~((std::uint64_t{1} << (vertex + 1)) - 1);
}

// Each K5 has a unique ordered triple of its three smallest vertices.  For
// every triangle a<b<c, count edges d-e in its common neighborhood with c<d<e.
std::uint16_t count_k5(const Rows& rows) {
  std::uint32_t total = 0;
  for (int a = 0; a < N; ++a) {
    std::uint64_t b_bits = rows[a] & greater_than(a);
    while (b_bits) {
      int b = std::countr_zero(b_bits);
      b_bits &= b_bits - 1;
      std::uint64_t c_bits = rows[a] & rows[b] & greater_than(b);
      while (c_bits) {
        int c = std::countr_zero(c_bits);
        c_bits &= c_bits - 1;
        std::uint64_t common = rows[a] & rows[b] & rows[c] & greater_than(c);
        std::uint64_t d_bits = common;
        while (d_bits) {
          int d = std::countr_zero(d_bits);
          d_bits &= d_bits - 1;
          total += std::popcount(rows[d] & common & greater_than(d));
        }
      }
    }
  }
  if (total > std::numeric_limits<std::uint16_t>::max()) fail("K5 count overflow");
  return static_cast<std::uint16_t>(total);
}

Rows complement(const Rows& rows) {
  Rows result{};
  for (int u = 0; u < N; ++u) {
    result[u] = VERTEX_MASK & ~rows[u] & ~(std::uint64_t{1} << u);
  }
  return result;
}

std::uint16_t burden(const Rows& rows) {
  return static_cast<std::uint16_t>(count_k5(rows) + count_k5(complement(rows)));
}

void toggle(Rows& rows, std::pair<int, int> edge) {
  const auto [u, v] = edge;
  rows[u] ^= std::uint64_t{1} << v;
  rows[v] ^= std::uint64_t{1} << u;
}

bool strict_predicate(std::pair<int, int> first, std::pair<int, int> second) {
  constexpr std::array<int, 4> shared{6, 12, 36, 42};
  for (int vertex : shared) {
    const bool first_survives = first.first != vertex && first.second != vertex;
    const bool second_survives = second.first != vertex && second.second != vertex;
    if (!first_survives && !second_survives) return false;
  }
  return true;
}

void write_u16le(std::ofstream& output, std::uint16_t value) {
  const char bytes[2] = {
      static_cast<char>(value & 0xff),
      static_cast<char>((value >> 8) & 0xff),
  };
  output.write(bytes, 2);
  if (!output) fail("failed to write score ledger");
}

void print_histogram(const std::map<int, std::uint64_t>& histogram) {
  std::cout << '{';
  bool first = true;
  for (const auto& [score, count] : histogram) {
    if (!first) std::cout << ',';
    first = false;
    std::cout << '"' << score << "\":" << count;
  }
  std::cout << '}';
}

void print_minimizers(const std::vector<std::array<int, 2>>& minimizers,
                      const std::vector<std::pair<int, int>>& edges) {
  std::cout << '[';
  for (std::size_t index = 0; index < minimizers.size(); ++index) {
    if (index) std::cout << ',';
    const int i = minimizers[index][0];
    const int j = minimizers[index][1];
    std::cout << "{\"edge_indices\":[" << i << ',' << j << "],\"edges\":[["
              << edges[i].first << ',' << edges[i].second << "],[" << edges[j].first
              << ',' << edges[j].second << "]] }";
  }
  std::cout << ']';
}

void print_single_minimizers(const std::vector<int>& minimizers,
                             const std::vector<std::pair<int, int>>& edges) {
  std::cout << '[';
  for (std::size_t index = 0; index < minimizers.size(); ++index) {
    if (index) std::cout << ',';
    const int edge_index = minimizers[index];
    std::cout << "{\"edge_index\":" << edge_index << ",\"edge\":["
              << edges[edge_index].first << ',' << edges[edge_index].second << "]}";
  }
  std::cout << ']';
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 2 && argc != 3) {
      std::cerr << "usage: adversarial_radius2_bitset MATRIX [OUTPUT_LEDGER]\n";
      return 2;
    }
    const Parsed parsed = parse_matrix(argv[1]);
    if (argc == 2) {
      std::cout << "{\"checker\":\"cpp20-triangle-common-neighborhood-bitsets\","
                << "\"order\":" << N << ",\"seed_edges\":" << parsed.edge_count
                << ",\"zero_k5\":" << count_k5(complement(parsed.rows))
                << ",\"one_k5\":" << count_k5(parsed.rows)
                << ",\"seed_burden\":" << burden(parsed.rows) << "}\n";
      return 0;
    }
    std::vector<std::pair<int, int>> edges;
    edges.reserve(EDGE_COUNT);
    for (int u = 0; u < N; ++u) {
      for (int v = u + 1; v < N; ++v) edges.emplace_back(u, v);
    }
    if (static_cast<int>(edges.size()) != EDGE_COUNT) fail("edge ordering cardinality mismatch");

    std::ofstream ledger(argv[2], std::ios::binary | std::ios::trunc);
    if (!ledger) fail("cannot create score ledger");

    Rows rows = parsed.rows;
    std::map<int, std::uint64_t> radius_one_histogram;
    int radius_one_minimum = std::numeric_limits<int>::max();
    std::vector<int> radius_one_minimizers;
    for (int index = 0; index < EDGE_COUNT; ++index) {
      toggle(rows, edges[index]);
      const int score = burden(rows);
      toggle(rows, edges[index]);
      ++radius_one_histogram[score];
      if (score < radius_one_minimum) {
        radius_one_minimum = score;
        radius_one_minimizers.clear();
      }
      if (score == radius_one_minimum) radius_one_minimizers.push_back(index);
    }
    std::map<int, std::uint64_t> histogram;
    std::map<int, std::uint64_t> strict_histogram;
    int minimum = std::numeric_limits<int>::max();
    int strict_minimum = std::numeric_limits<int>::max();
    std::uint64_t pair_count = 0;
    std::uint64_t strict_count = 0;
    std::vector<std::array<int, 2>> minimizers;
    std::vector<std::array<int, 2>> strict_minimizers;

    for (int i = 0; i < EDGE_COUNT - 1; ++i) {
      toggle(rows, edges[i]);
      for (int j = i + 1; j < EDGE_COUNT; ++j) {
        toggle(rows, edges[j]);
        const int score = burden(rows);
        toggle(rows, edges[j]);
        write_u16le(ledger, static_cast<std::uint16_t>(score));
        ++pair_count;
        ++histogram[score];
        if (score < minimum) {
          minimum = score;
          minimizers.clear();
        }
        if (score == minimum) minimizers.push_back({i, j});

        if (strict_predicate(edges[i], edges[j])) {
          ++strict_count;
          ++strict_histogram[score];
          if (score < strict_minimum) {
            strict_minimum = score;
            strict_minimizers.clear();
          }
          if (score == strict_minimum) strict_minimizers.push_back({i, j});
        }
      }
      toggle(rows, edges[i]);
    }
    ledger.close();
    if (rows != parsed.rows) fail("toggle restoration mismatch");

    std::cout << "{\"checker\":\"cpp20-triangle-common-neighborhood-bitsets\","
              << "\"order\":" << N << ",\"seed_edges\":" << parsed.edge_count
              << ",\"seed_burden\":" << burden(parsed.rows)
              << ",\"edge_count\":" << edges.size()
              << ",\"radius_one_minimum\":" << radius_one_minimum
              << ",\"radius_one_minimizers\":";
    print_single_minimizers(radius_one_minimizers, edges);
    std::cout << ",\"radius_one_histogram\":";
    print_histogram(radius_one_histogram);
    std::cout << ",\"pair_count\":" << pair_count << ",\"minimum\":" << minimum
              << ",\"minimizers\":";
    print_minimizers(minimizers, edges);
    std::cout << ",\"histogram\":";
    print_histogram(histogram);
    std::cout << ",\"strict_pair_count\":" << strict_count
              << ",\"strict_minimum\":" << strict_minimum << ",\"strict_minimizers\":";
    print_minimizers(strict_minimizers, edges);
    std::cout << ",\"strict_histogram\":";
    print_histogram(strict_histogram);
    std::cout << "}\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "adversarial_radius2_bitset: " << error.what() << '\n';
    return 2;
  }
}
