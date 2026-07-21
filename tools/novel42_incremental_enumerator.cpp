#include <cadical.hpp>

#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

class WallTerminator final : public CaDiCaL::Terminator {
 public:
  void reset(double seconds) {
    deadline_ = std::chrono::steady_clock::now() +
                std::chrono::milliseconds(static_cast<long long>(seconds * 1000.0));
  }
  bool terminate() override { return std::chrono::steady_clock::now() >= deadline_; }

 private:
  std::chrono::steady_clock::time_point deadline_;
};

int parse_positive(const char* text, const char* name) {
  char* end = nullptr;
  const long value = std::strtol(text, &end, 10);
  if (!text[0] || *end || value <= 0 || value > 2000000000L) {
    throw std::runtime_error(std::string("invalid ") + name);
  }
  return static_cast<int>(value);
}

double parse_seconds(const char* text) {
  char* end = nullptr;
  const double value = std::strtod(text, &end);
  if (!text[0] || *end || value <= 0.0) throw std::runtime_error("invalid solve seconds");
  return value;
}

void write_model(const std::string& path, CaDiCaL::Solver& solver, int variables) {
  std::vector<unsigned char> packed((variables + 7) / 8, 0);
  for (int variable = 1; variable <= variables; ++variable) {
    if (solver.val(variable) > 0) {
      const int bit = variable - 1;
      packed[bit / 8] |= static_cast<unsigned char>(1U << (bit % 8));
    }
  }
  std::ofstream stream(path, std::ios::binary);
  if (!stream) throw std::runtime_error("cannot open model output");
  stream.write(reinterpret_cast<const char*>(packed.data()),
               static_cast<std::streamsize>(packed.size()));
  if (!stream) throw std::runtime_error("cannot write model output");
}

}  // namespace

int main(int argc, char** argv) try {
  if (argc != 8) {
    std::cerr << "usage: novel42_incremental_enumerator BASE_CNF OUTPUT_DIR "
                 "TOTAL_VARS PRIMARY_VARS MAX_MODELS SEED SOLVE_SECONDS\n";
    return 2;
  }
  const std::string base_cnf = argv[1];
  const std::string output_dir = argv[2];
  const int total_variables = parse_positive(argv[3], "total variables");
  const int primary_variables = parse_positive(argv[4], "primary variables");
  const int max_models = parse_positive(argv[5], "model limit");
  const int seed = parse_positive(argv[6], "seed");
  const double solve_seconds = parse_seconds(argv[7]);
  if (primary_variables > total_variables) throw std::runtime_error("primary range exceeds total range");

  CaDiCaL::Solver solver;
  solver.set("quiet", 1);
  solver.set("seed", seed);
  int parsed_variables = 0;
  if (const char* error = solver.read_dimacs(base_cnf.c_str(), parsed_variables, 1)) {
    throw std::runtime_error(std::string("DIMACS parse failed: ") + error);
  }
  if (parsed_variables != total_variables) throw std::runtime_error("DIMACS variable count mismatch");

  WallTerminator terminator;
  solver.connect_terminator(&terminator);
  for (int round = 1; round <= max_models; ++round) {
    terminator.reset(solve_seconds);
    const auto started = std::chrono::steady_clock::now();
    const int result = solver.solve();
    const double elapsed = std::chrono::duration<double>(
                               std::chrono::steady_clock::now() - started)
                               .count();
    if (result == 10) {
      char name[64];
      std::snprintf(name, sizeof(name), "model-%03d.bits", round);
      const std::string path = output_dir + "/" + name;
      std::vector<int> primary(primary_variables + 1);
      for (int variable = 1; variable <= primary_variables; ++variable)
        primary[variable] = solver.val(variable);
      write_model(path, solver, total_variables);
      std::cout << "{\"status\":\"SAT\",\"round\":" << round
                << ",\"seconds\":" << elapsed << ",\"model\":\"" << name
                << "\",\"cadical_version\":\"" << CaDiCaL::Solver::version()
                << "\"}" << std::endl;
      std::string command;
      if (!std::getline(std::cin, command)) throw std::runtime_error("controller closed protocol");
      if (command == "STOP") break;
      if (command != "CONTINUE") throw std::runtime_error("invalid controller command");
      for (int variable = 1; variable <= primary_variables; ++variable)
        solver.add(primary[variable] > 0 ? -variable : variable);
      solver.add(0);
    } else if (result == 20) {
      std::cout << "{\"status\":\"UNSAT_UNVERIFIED\",\"round\":" << round
                << ",\"seconds\":" << elapsed << "}" << std::endl;
      break;
    } else {
      std::cout << "{\"status\":\"UNKNOWN\",\"round\":" << round
                << ",\"seconds\":" << elapsed << "}" << std::endl;
      break;
    }
  }
  solver.disconnect_terminator();
  return 0;
} catch (const std::exception& error) {
  std::cerr << "incremental enumerator error: " << error.what() << '\n';
  return 1;
}
