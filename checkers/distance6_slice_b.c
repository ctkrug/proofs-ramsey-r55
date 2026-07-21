#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>

#define ORDER 43
#define MAX_CONSTRAINTS 256
#define MAX_MODELS 512
#define TITLE "# Supplementary Data 4: The coloring matrix with only 2 monochromatic 5-cliques of a complete graph with 43 nodes"

typedef struct {
    int positive;
    int length;
    int variables[3];
    int multiplicity;
} Constraint;

static int matrix[ORDER][ORDER];
static Constraint constraints[MAX_CONSTRAINTS];
static int constraint_count = 0;
static uint64_t models[MAX_MODELS];
static int model_count = 0;
static int disabled[MAX_CONSTRAINTS];

static void fail(const char *message) {
    fprintf(stderr, "distance6_slice_b: %s\n", message);
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
        line[--length] = '\0';
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
        for (int v = u + 1; v < ORDER; ++v) {
            if (matrix[u][v] != matrix[v][u]) fail("asymmetric matrix");
        }
    }
}

static int compare_int(const void *left, const void *right) {
    return *(const int *)left - *(const int *)right;
}

static void add_constraint(int positive, int length, int variables[3]) {
    if (length < 1 || length > 3) fail("active five-set has unexpected variable count");
    qsort(variables, (size_t)length, sizeof(int), compare_int);
    for (int index = 0; index < constraint_count; ++index) {
        Constraint *item = &constraints[index];
        if (item->positive == positive && item->length == length &&
            !memcmp(item->variables, variables, (size_t)length * sizeof(int))) {
            item->multiplicity += 1;
            return;
        }
    }
    if (constraint_count >= MAX_CONSTRAINTS) fail("constraint storage overflow");
    Constraint *item = &constraints[constraint_count++];
    item->positive = positive;
    item->length = length;
    item->multiplicity = 1;
    memcpy(item->variables, variables, (size_t)length * sizeof(int));
}

static int variable_for_edge(int u, int v) {
    int difference = v - u;
    if (difference == 6) return u;
    if (difference == ORDER - 6) return v;
    return -1;
}

static void process_five_set(int vertices[5]) {
    int variables[10] = {0};
    int variable_count = 0;
    int fixed_count = 0;
    int fixed_ones = 0;
    for (int i = 0; i < 5; ++i) {
        for (int j = i + 1; j < 5; ++j) {
            int u = vertices[i];
            int v = vertices[j];
            int variable = variable_for_edge(u, v);
            if (variable >= 0) {
                variables[variable_count++] = variable;
            } else {
                fixed_count += 1;
                fixed_ones += matrix[u][v];
            }
        }
    }
    if (fixed_count && fixed_ones == 0) add_constraint(1, variable_count, variables);
    if (fixed_count && fixed_ones == fixed_count) add_constraint(0, variable_count, variables);
}

static void derive_constraints(void) {
    int vertices[5];
    for (vertices[0] = 0; vertices[0] < ORDER; ++vertices[0])
    for (vertices[1] = vertices[0] + 1; vertices[1] < ORDER; ++vertices[1])
    for (vertices[2] = vertices[1] + 1; vertices[2] < ORDER; ++vertices[2])
    for (vertices[3] = vertices[2] + 1; vertices[3] < ORDER; ++vertices[3])
    for (vertices[4] = vertices[3] + 1; vertices[4] < ORDER; ++vertices[4])
        process_five_set(vertices);
}

static int constraint_satisfied(const Constraint *item, const int assignment[ORDER]) {
    for (int i = 0; i < item->length; ++i) {
        int value = assignment[item->variables[i]];
        if ((item->positive && value == 1) || (!item->positive && value == 0)) return 1;
    }
    return 0;
}

static int actual_burden(const int assignment[ORDER]) {
    int total = 0;
    for (int index = 0; index < constraint_count; ++index) {
        if (!constraint_satisfied(&constraints[index], assignment)) {
            total += constraints[index].multiplicity;
        }
    }
    return total;
}

static void add_model(const int assignment[ORDER], int maximum_burden) {
    if (actual_burden(assignment) > maximum_burden) return;
    uint64_t word = 0;
    for (int variable = 0; variable < ORDER; ++variable) {
        if (assignment[variable]) word |= UINT64_C(1) << variable;
    }
    for (int index = 0; index < model_count; ++index) {
        if (models[index] == word) return;
    }
    if (model_count >= MAX_MODELS) fail("model storage overflow");
    models[model_count++] = word;
}

static int propagate(int assignment[ORDER]) {
    int changed;
    do {
        changed = 0;
        for (int index = 0; index < constraint_count; ++index) {
            if (disabled[index]) continue;
            const Constraint *item = &constraints[index];
            int satisfied = 0;
            int unassigned = 0;
            int last = -1;
            for (int i = 0; i < item->length; ++i) {
                int variable = item->variables[i];
                int value = assignment[variable];
                if (value < 0) {
                    unassigned += 1;
                    last = variable;
                } else if ((item->positive && value == 1) || (!item->positive && value == 0)) {
                    satisfied = 1;
                    break;
                }
            }
            if (satisfied) continue;
            if (unassigned == 0) return 0;
            if (unassigned == 1) {
                int required = item->positive ? 1 : 0;
                if (assignment[last] >= 0 && assignment[last] != required) return 0;
                if (assignment[last] < 0) {
                    assignment[last] = required;
                    changed = 1;
                }
            }
        }
    } while (changed);
    return 1;
}

static int choose_variable(const int assignment[ORDER]) {
    int scores[ORDER] = {0};
    for (int index = 0; index < constraint_count; ++index) {
        if (disabled[index]) continue;
        const Constraint *item = &constraints[index];
        if (constraint_satisfied(item, assignment)) continue;
        for (int i = 0; i < item->length; ++i) {
            int variable = item->variables[i];
            if (assignment[variable] < 0) scores[variable] += 1;
        }
    }
    int selected = -1;
    for (int variable = 0; variable < ORDER; ++variable) {
        if (assignment[variable] < 0 && (selected < 0 || scores[variable] > scores[selected])) {
            selected = variable;
        }
    }
    return selected;
}

static void search(int assignment[ORDER], int maximum_burden) {
    if (!propagate(assignment)) return;
    int variable = choose_variable(assignment);
    if (variable < 0) {
        add_model(assignment, maximum_burden);
        return;
    }
    for (int value = 0; value <= 1; ++value) {
        int child[ORDER];
        memcpy(child, assignment, sizeof(child));
        child[variable] = value;
        search(child, maximum_burden);
    }
}

static void force_false(int constraint_index, int assignment[ORDER]) {
    const Constraint *item = &constraints[constraint_index];
    int value = item->positive ? 0 : 1;
    for (int i = 0; i < item->length; ++i) {
        int variable = item->variables[i];
        if (assignment[variable] >= 0 && assignment[variable] != value) fail("relaxation force conflict");
        assignment[variable] = value;
    }
}

static void solve_relaxation(int first, int second, int maximum_burden) {
    int assignment[ORDER];
    for (int variable = 0; variable < ORDER; ++variable) assignment[variable] = -1;
    memset(disabled, 0, sizeof(disabled));
    if (first >= 0) {
        disabled[first] = 1;
        force_false(first, assignment);
    }
    if (second >= 0) {
        disabled[second] = 1;
        force_false(second, assignment);
    }
    search(assignment, maximum_burden);
}

static int compare_word(const void *left, const void *right) {
    uint64_t a = *(const uint64_t *)left;
    uint64_t b = *(const uint64_t *)right;
    return (a > b) - (a < b);
}

static void print_words(void) {
    qsort(models, (size_t)model_count, sizeof(uint64_t), compare_word);
    putchar('[');
    for (int index = 0; index < model_count; ++index) {
        if (index) putchar(',');
        putchar('"');
        for (int variable = 0; variable < ORDER; ++variable) {
            putchar((models[index] >> variable) & UINT64_C(1) ? '1' : '0');
        }
        putchar('"');
    }
    putchar(']');
}

static void print_constraint_family(int positive) {
    putchar('[');
    int printed = 0;
    for (int index = 0; index < constraint_count; ++index) {
        Constraint *item = &constraints[index];
        if (item->positive != positive) continue;
        if (printed++) putchar(',');
        putchar('[');
        for (int i = 0; i < item->length; ++i) {
            if (i) putchar(',');
            printf("%d", item->variables[i]);
        }
        putchar(']');
    }
    putchar(']');
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: %s MATRIX\n", argv[0]);
        return 2;
    }
    parse_matrix(argv[1]);
    derive_constraints();
    int positive_count = 0;
    int negative_count = 0;
    int raw_count = 0;
    for (int index = 0; index < constraint_count; ++index) {
        Constraint *item = &constraints[index];
        raw_count += item->multiplicity;
        if (item->positive) {
            positive_count += 1;
            if (item->length != 2 || item->multiplicity != 2) fail("unexpected positive constraint");
        } else {
            negative_count += 1;
            if (item->length != 3 || item->multiplicity != 1) fail("unexpected negative constraint");
        }
    }
    if (constraint_count != 129 || positive_count != 86 || negative_count != 43 || raw_count != 215) {
        fail("unexpected reduced-constraint cardinality");
    }

    model_count = 0;
    solve_relaxation(-1, -1, 0);
    int zero_models = model_count;

    model_count = 0;
    for (int index = 0; index < constraint_count; ++index) {
        if (!constraints[index].positive) solve_relaxation(index, -1, 1);
    }
    int one_models = model_count;

    model_count = 0;
    for (int index = 0; index < constraint_count; ++index) {
        if (constraints[index].positive) solve_relaxation(index, -1, 2);
    }
    for (int first = 0; first < constraint_count; ++first) {
        if (constraints[first].positive) continue;
        for (int second = first + 1; second < constraint_count; ++second) {
            if (!constraints[second].positive) solve_relaxation(first, second, 2);
        }
    }

    printf("{\"checker\":\"c-relaxation-case-dpll\",\"order\":43,");
    printf("\"raw_active_five_sets\":%d,\"unique_constraints\":%d,", raw_count, constraint_count);
    printf("\"positive_pairs\":");
    print_constraint_family(1);
    printf(",\"positive_pair_multiplicity\":2,\"negative_triples\":");
    print_constraint_family(0);
    printf(",\"negative_triple_multiplicity\":1,");
    printf("\"burden_at_most\":{\"0\":\"%s\",\"1\":\"%s\",\"2\":\"%s\"},",
           zero_models ? "sat" : "unsat", one_models ? "sat" : "unsat", model_count ? "sat" : "unsat");
    printf("\"minimum_burden\":2,\"minimum_model_count\":%d,\"minimum_words_u_order\":", model_count);
    print_words();
    printf("}\n");
    return 0;
}
