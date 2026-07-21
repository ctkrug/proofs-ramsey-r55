#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>

#define ORDER 43
#define MAX_ORIGINS 100000
#define TITLE "# Supplementary Data 4: The coloring matrix with only 2 monochromatic 5-cliques of a complete graph with 43 nodes"

typedef struct { int length; int literals[10]; } OriginClause;

static int matrix[ORDER][ORDER];
static OriginClause *origins;
static int origin_count;
static int all_variable_count;
static int mode;
static int graph_variables;
static FILE *ledger;
static FILE *mapping;

static void fail(const char *message) {
    fprintf(stderr, "two_orbit_burden_b: %s\n", message);
    exit(2);
}

static void parse_matrix(const char *path) {
    FILE *stream = fopen(path, "rb");
    if (!stream) fail("could not open matrix");
    char *line = NULL;
    size_t capacity = 0;
    ssize_t length = getline(&line, &capacity, stream);
    if (length < 0 || line[length - 1] != '\n') fail("publisher title is absent or not LF terminated");
    line[--length] = '\0';
    if (strcmp(line, TITLE)) fail("publisher title mismatch");
    for (int row = 0; row < ORDER; ++row) {
        length = getline(&line, &capacity, stream);
        if (length != 2 * ORDER || line[length - 1] != '\n') fail("publisher row width mismatch");
        for (int column = 0; column < ORDER; ++column) {
            char value = line[2 * column];
            if (value != '0' && value != '1') fail("nonbinary publisher token");
            if (column + 1 < ORDER && line[2 * column + 1] != ' ') fail("publisher separator mismatch");
            matrix[row][column] = value - '0';
        }
    }
    if (getline(&line, &capacity, stream) >= 0) fail("extra line after publisher matrix");
    free(line);
    fclose(stream);
    for (int u = 0; u < ORDER; ++u) {
        if (matrix[u][u]) fail("nonzero diagonal");
        for (int v = u + 1; v < ORDER; ++v)
            if (matrix[u][v] != matrix[v][u]) fail("asymmetric matrix");
    }
}

static int integer_compare(const void *left, const void *right) {
    return *(const int *)left - *(const int *)right;
}

static int orbit_index(int u, int v, int distance) {
    int difference = v - u;
    if (difference == distance) return u;
    if (difference == ORDER - distance) return v;
    return -1;
}

static int variable_id(int u, int v) {
    int index = orbit_index(u, v, 6);
    if (index >= 0) return index + 1;
    if (mode) {
        index = orbit_index(u, v, mode);
        if (index >= 0) return ORDER + index + 1;
    }
    return 0;
}

static void record_origin(const int vertices[5], int color, int variables[10], int variable_count,
                          int fixed_u[10], int fixed_v[10], int fixed_value[10], int fixed_count) {
    if (origin_count >= MAX_ORIGINS) fail("origin storage overflow");
    OriginClause *origin = &origins[origin_count];
    origin->length = variable_count;
    for (int i = 0; i < variable_count; ++i)
        origin->literals[i] = color ? -variables[i] : variables[i];
    qsort(origin->literals, (size_t)variable_count, sizeof(int), integer_compare);
    for (int i = 0; i < 5; ++i) fprintf(ledger, "%s%d", i ? "," : "", vertices[i]);
    fprintf(ledger, "|%d|", color);
    for (int i = 0; i < variable_count; ++i)
        fprintf(ledger, "%s%d", i ? "," : "", origin->literals[i]);
    fputc('|', ledger);
    for (int i = 0; i < fixed_count; ++i)
        fprintf(ledger, "%s%d-%d=%d", i ? "," : "", fixed_u[i], fixed_v[i], fixed_value[i]);
    fputc('\n', ledger);
    int relaxation = graph_variables + origin_count + 1;
    fprintf(mapping, "%d|%d|", origin_count + 1, relaxation);
    for (int i = 0; i < 5; ++i) fprintf(mapping, "%s%d", i ? "," : "", vertices[i]);
    fprintf(mapping, "|%d\n", color);
    origin_count += 1;
}

static void process_five_set(const int vertices[5]) {
    int variables[10], variable_count = 0;
    int fixed_u[10], fixed_v[10], fixed_value[10], fixed_count = 0;
    for (int i = 0; i < 5; ++i) for (int j = i + 1; j < 5; ++j) {
        int u = vertices[i], v = vertices[j];
        int variable = variable_id(u, v);
        if (variable) variables[variable_count++] = variable;
        else {
            fixed_u[fixed_count] = u;
            fixed_v[fixed_count] = v;
            fixed_value[fixed_count++] = matrix[u][v];
        }
    }
    if (!fixed_count) all_variable_count += 1;
    for (int color = 0; color <= 1; ++color) {
        int active = 1;
        for (int i = 0; i < fixed_count; ++i)
            if (fixed_value[i] != color) { active = 0; break; }
        if (active)
            record_origin(vertices, color, variables, variable_count,
                          fixed_u, fixed_v, fixed_value, fixed_count);
    }
}

static int relaxation_variable(int position) {
    /* position is one-based. */
    return graph_variables + position;
}

static int suffix_variable(int position) {
    /* t_position for position in 2..origin_count. */
    return graph_variables + origin_count + position - 1;
}

static void write_binary_clause(FILE *stream, int first, int second) {
    fprintf(stream, "%d %d 0\n", first, second);
}

int main(int argc, char **argv) {
    if (argc != 7) {
        fprintf(stderr, "usage: %s MATRIX MODE CNF LEDGER MAPPING SUMMARY\n", argv[0]);
        return 2;
    }
    mode = atoi(argv[2]);
    if (mode != 0 && (mode < 1 || mode > 21 || mode == 6)) fail("invalid mode");
    graph_variables = mode ? 2 * ORDER : ORDER;
    parse_matrix(argv[1]);
    origins = calloc(MAX_ORIGINS, sizeof(OriginClause));
    if (!origins) fail("could not allocate origin storage");
    ledger = fopen(argv[4], "wb");
    mapping = fopen(argv[5], "wb");
    if (!ledger || !mapping) fail("could not open ledger or mapping output");
    int vertices[5];
    for (vertices[0] = 0; vertices[0] < ORDER; ++vertices[0])
    for (vertices[1] = vertices[0] + 1; vertices[1] < ORDER; ++vertices[1])
    for (vertices[2] = vertices[1] + 1; vertices[2] < ORDER; ++vertices[2])
    for (vertices[3] = vertices[2] + 1; vertices[3] < ORDER; ++vertices[3])
    for (vertices[4] = vertices[3] + 1; vertices[4] < ORDER; ++vertices[4])
        process_five_set(vertices);
    if (fclose(ledger) || fclose(mapping)) fail("could not close ledger or mapping output");
    if (origin_count < 2) fail("unexpectedly small raw-origin set");

    int amo_clauses = 3 * origin_count - 4;
    int clause_count = origin_count + amo_clauses;
    int variable_count = graph_variables + 2 * origin_count - 1;
    FILE *cnf = fopen(argv[3], "wb");
    if (!cnf) fail("could not open CNF output");
    fprintf(cnf, "p cnf %d %d\n", variable_count, clause_count);
    for (int index = 0; index < origin_count; ++index) {
        for (int j = 0; j < origins[index].length; ++j)
            fprintf(cnf, "%d ", origins[index].literals[j]);
        fprintf(cnf, "%d 0\n", relaxation_variable(index + 1));
    }
    /* Independent suffix AMO: t_i means that some r_i,...,r_m is true. */
    write_binary_clause(cnf, -relaxation_variable(origin_count), suffix_variable(origin_count));
    for (int position = origin_count - 1; position >= 2; --position) {
        write_binary_clause(cnf, -relaxation_variable(position), suffix_variable(position));
        write_binary_clause(cnf, -suffix_variable(position + 1), suffix_variable(position));
        write_binary_clause(cnf, -relaxation_variable(position), -suffix_variable(position + 1));
    }
    write_binary_clause(cnf, -relaxation_variable(1), -suffix_variable(2));
    if (fclose(cnf)) fail("could not close CNF output");

    int maximum_length = 0;
    for (int index = 0; index < origin_count; ++index)
        if (origins[index].length > maximum_length) maximum_length = origins[index].length;
    FILE *summary = fopen(argv[6], "wb");
    if (!summary) fail("could not open summary output");
    fprintf(summary, "{\"all_variable_five_sets\":%d,\"amo_clauses\":%d,", all_variable_count, amo_clauses);
    fprintf(summary, "\"auxiliary_variables\":%d,\"cardinality_bound\":1,", origin_count - 1);
    fprintf(summary, "\"cardinality_encoding\":\"suffix sequential AMO\",\"checker\":\"c-nested-loop-suffix-sequential-amo\",");
    fprintf(summary, "\"clauses\":%d,\"duplicates_preserved\":true,\"graph_variables\":%d,", clause_count, graph_variables);
    fprintf(summary, "\"maximum_origin_clause_length\":%d,\"mode\":%d,\"order\":43,", maximum_length, mode);
    fprintf(summary, "\"raw_active_origins\":%d,\"relaxation_variables\":%d,", origin_count, origin_count);
    fprintf(summary, "\"relaxed_origin_clauses\":%d,\"variables\":%d}\n", origin_count, variable_count);
    if (fclose(summary)) fail("could not close summary output");
    free(origins);
    return 0;
}
