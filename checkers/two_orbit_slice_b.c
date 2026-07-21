#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>

#define ORDER 43
#define MAX_ORIGINS 1925196
#define TITLE "# Supplementary Data 4: The coloring matrix with only 2 monochromatic 5-cliques of a complete graph with 43 nodes"

typedef struct { int length; int literals[10]; } Clause;

static int matrix[ORDER][ORDER];
static Clause *clauses;
static int clause_count;
static int all_variable_count;
static int second_distance;
static FILE *ledger;

static void fail(const char *message) {
    fprintf(stderr, "two_orbit_slice_b: %s\n", message);
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
        for (int v = u + 1; v < ORDER; ++v) if (matrix[u][v] != matrix[v][u]) fail("asymmetric matrix");
    }
}

static int integer_compare(const void *left, const void *right) {
    return *(const int *)left - *(const int *)right;
}

static int clause_compare(const void *left, const void *right) {
    const Clause *a = left, *b = right;
    int common = a->length < b->length ? a->length : b->length;
    for (int i = 0; i < common; ++i) {
        if (a->literals[i] != b->literals[i]) return a->literals[i] - b->literals[i];
    }
    return a->length - b->length;
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
    index = orbit_index(u, v, second_distance);
    if (index >= 0) return ORDER + index + 1;
    return 0;
}

static void record_origin(const int vertices[5], int color, int variables[10], int variable_count,
                          int fixed_u[10], int fixed_v[10], int fixed_value[10], int fixed_count) {
    if (clause_count >= MAX_ORIGINS) fail("origin storage overflow");
    Clause *clause = &clauses[clause_count++];
    clause->length = variable_count;
    for (int i = 0; i < variable_count; ++i) clause->literals[i] = color ? -variables[i] : variables[i];
    qsort(clause->literals, (size_t)variable_count, sizeof(int), integer_compare);
    for (int i = 0; i < 5; ++i) fprintf(ledger, "%s%d", i ? "," : "", vertices[i]);
    fprintf(ledger, "|%d|", color);
    for (int i = 0; i < variable_count; ++i) fprintf(ledger, "%s%d", i ? "," : "", clause->literals[i]);
    fputc('|', ledger);
    for (int i = 0; i < fixed_count; ++i)
        fprintf(ledger, "%s%d-%d=%d", i ? "," : "", fixed_u[i], fixed_v[i], fixed_value[i]);
    fputc('\n', ledger);
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
        for (int i = 0; i < fixed_count; ++i) if (fixed_value[i] != color) { active = 0; break; }
        if (active) record_origin(vertices, color, variables, variable_count, fixed_u, fixed_v, fixed_value, fixed_count);
    }
}

static int same_clause(const Clause *a, const Clause *b) {
    return a->length == b->length && !memcmp(a->literals, b->literals, (size_t)a->length * sizeof(int));
}

int main(int argc, char **argv) {
    if (argc != 6) {
        fprintf(stderr, "usage: %s MATRIX SECOND_DISTANCE CNF LEDGER SUMMARY\n", argv[0]);
        return 2;
    }
    second_distance = atoi(argv[2]);
    if (second_distance < 1 || second_distance > 21 || second_distance == 6) fail("invalid second distance");
    parse_matrix(argv[1]);
    clauses = calloc(MAX_ORIGINS, sizeof(Clause));
    if (!clauses) fail("could not allocate origin storage");
    ledger = fopen(argv[4], "wb");
    if (!ledger) fail("could not open ledger output");
    int vertices[5];
    for (vertices[0] = 0; vertices[0] < ORDER; ++vertices[0])
    for (vertices[1] = vertices[0] + 1; vertices[1] < ORDER; ++vertices[1])
    for (vertices[2] = vertices[1] + 1; vertices[2] < ORDER; ++vertices[2])
    for (vertices[3] = vertices[2] + 1; vertices[3] < ORDER; ++vertices[3])
    for (vertices[4] = vertices[3] + 1; vertices[4] < ORDER; ++vertices[4]) process_five_set(vertices);
    if (fclose(ledger)) fail("could not close ledger output");
    qsort(clauses, (size_t)clause_count, sizeof(Clause), clause_compare);
    int unique = 0, maximum_length = 0, has_empty = 0;
    for (int i = 0; i < clause_count; ++i) {
        if (i && same_clause(&clauses[i - 1], &clauses[i])) continue;
        unique += 1;
        if (clauses[i].length > maximum_length) maximum_length = clauses[i].length;
        if (!clauses[i].length) has_empty = 1;
    }
    FILE *cnf = fopen(argv[3], "wb");
    if (!cnf) fail("could not open CNF output");
    fprintf(cnf, "p cnf %d %d\n", 2 * ORDER, unique);
    for (int i = 0; i < clause_count; ++i) {
        if (i && same_clause(&clauses[i - 1], &clauses[i])) continue;
        for (int j = 0; j < clauses[i].length; ++j) fprintf(cnf, "%d ", clauses[i].literals[j]);
        fprintf(cnf, "0\n");
    }
    if (fclose(cnf)) fail("could not close CNF output");
    FILE *summary = fopen(argv[5], "wb");
    if (!summary) fail("could not open summary output");
    fprintf(summary, "{\"all_variable_five_sets\":%d,\"checker\":\"c-nested-loop-direct-five-set-derivation\",", all_variable_count);
    fprintf(summary, "\"empty_clause\":%s,\"maximum_clause_length\":%d,", has_empty ? "true" : "false", maximum_length);
    fprintf(summary, "\"order\":43,\"raw_active_origins\":%d,\"second_distance\":%d,", clause_count, second_distance);
    fprintf(summary, "\"unique_clauses\":%d,\"variables\":86}\n", unique);
    if (fclose(summary)) fail("could not close summary output");
    free(clauses);
    return 0;
}
