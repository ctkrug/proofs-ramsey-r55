#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>

#define ORDER 43
#define EDGE_COUNT 903
#define PAIR_COUNT 407253
#define MAX_K5 962598
#define TITLE "# Supplementary Data 4: The coloring matrix with only 2 monochromatic 5-cliques of a complete graph with 43 nodes"

typedef struct {
    int u;
    int v;
} Edge;

typedef struct {
    int count;
    int vertices[MAX_K5][5];
} CliqueList;

static uint64_t adjacency[ORDER];
static Edge edges[EDGE_COUNT];

static void fail(const char *message) {
    fprintf(stderr, "%s\n", message);
    exit(1);
}

static void build_edges(void) {
    int index = 0;
    for (int u = 0; u < ORDER; ++u) {
        for (int v = u + 1; v < ORDER; ++v) {
            edges[index++] = (Edge){u, v};
        }
    }
    if (index != EDGE_COUNT) {
        fail("internal edge cardinality mismatch");
    }
}

static void parse_matrix(const char *path) {
    FILE *stream = fopen(path, "rb");
    if (stream == NULL) {
        fail("could not open matrix");
    }
    char *line = NULL;
    size_t capacity = 0;
    ssize_t length = getline(&line, &capacity, stream);
    if (length < 0 || line[length - 1] != '\n') {
        fail("publisher title is absent or not LF terminated");
    }
    line[--length] = '\0';
    if (strcmp(line, TITLE) != 0) {
        fail("publisher title mismatch");
    }
    int values[ORDER][ORDER] = {{0}};
    for (int row = 0; row < ORDER; ++row) {
        length = getline(&line, &capacity, stream);
        if (length != 2 * ORDER || line[length - 1] != '\n') {
            fail("publisher row has the wrong width or line ending");
        }
        line[--length] = '\0';
        for (int column = 0; column < ORDER; ++column) {
            char value = line[2 * column];
            if (value != '0' && value != '1') {
                fail("matrix must contain only 0 and 1");
            }
            values[row][column] = value - '0';
            if (column + 1 < ORDER && line[2 * column + 1] != ' ') {
                fail("publisher row tokens must be separated by one space");
            }
        }
    }
    if (getline(&line, &capacity, stream) >= 0) {
        fail("extra line after publisher matrix");
    }
    if (ferror(stream)) {
        fail("could not read matrix");
    }
    free(line);
    fclose(stream);
    for (int u = 0; u < ORDER; ++u) {
        if (values[u][u] != 0) {
            fail("matrix diagonal must be zero");
        }
        for (int v = u + 1; v < ORDER; ++v) {
            if (values[u][v] != values[v][u]) {
                fail("matrix must be symmetric");
            }
            if (values[u][v]) {
                adjacency[u] |= UINT64_C(1) << v;
                adjacency[v] |= UINT64_C(1) << u;
            }
        }
    }
}

static uint64_t search_adjacency[ORDER];

static uint32_t count_recursive(uint64_t candidates, int depth) {
    if (depth == 5) {
        return 1;
    }
    if (__builtin_popcountll(candidates) < 5 - depth) {
        return 0;
    }
    uint32_t total = 0;
    while (candidates) {
        int vertex = __builtin_ctzll(candidates);
        candidates &= candidates - 1;
        total += count_recursive(candidates & search_adjacency[vertex], depth + 1);
    }
    return total;
}

static uint32_t count_all_violations(void) {
    const uint64_t universe = (UINT64_C(1) << ORDER) - UINT64_C(1);
    for (int u = 0; u < ORDER; ++u) {
        search_adjacency[u] = adjacency[u];
    }
    uint32_t ones = count_recursive(universe, 0);
    for (int u = 0; u < ORDER; ++u) {
        search_adjacency[u] = universe & ~(UINT64_C(1) << u) & ~adjacency[u];
    }
    uint32_t zeros = count_recursive(universe, 0);
    return ones + zeros;
}

static void collect_recursive(uint64_t candidates, int depth, int selected[5], CliqueList *output) {
    if (depth == 5) {
        if (output->count >= MAX_K5) {
            fail("clique output overflow");
        }
        for (int i = 0; i < 5; ++i) {
            output->vertices[output->count][i] = selected[i];
        }
        output->count += 1;
        return;
    }
    if (__builtin_popcountll(candidates) < 5 - depth) {
        return;
    }
    while (candidates) {
        int vertex = __builtin_ctzll(candidates);
        candidates &= candidates - 1;
        selected[depth] = vertex;
        collect_recursive(candidates & search_adjacency[vertex], depth + 1, selected, output);
    }
}

static CliqueList *collect_cliques(int complement) {
    const uint64_t universe = (UINT64_C(1) << ORDER) - UINT64_C(1);
    for (int u = 0; u < ORDER; ++u) {
        if (complement) {
            search_adjacency[u] = universe & ~(UINT64_C(1) << u) & ~adjacency[u];
        } else {
            search_adjacency[u] = adjacency[u];
        }
    }
    CliqueList *output = calloc(1, sizeof(*output));
    if (output == NULL) {
        fail("could not allocate clique output");
    }
    int selected[5] = {0, 0, 0, 0, 0};
    collect_recursive(universe, 0, selected, output);
    return output;
}

static void toggle_edge(int edge_index) {
    Edge edge = edges[edge_index];
    adjacency[edge.u] ^= UINT64_C(1) << edge.v;
    adjacency[edge.v] ^= UINT64_C(1) << edge.u;
}

static void print_clique_list(const CliqueList *list) {
    putchar('[');
    for (int i = 0; i < list->count; ++i) {
        if (i) {
            putchar(',');
        }
        printf("[%d,%d,%d,%d,%d]", list->vertices[i][0], list->vertices[i][1],
               list->vertices[i][2], list->vertices[i][3], list->vertices[i][4]);
    }
    putchar(']');
}

static void print_record(int first, int second) {
    toggle_edge(first);
    toggle_edge(second);
    CliqueList *ones = collect_cliques(0);
    CliqueList *zeros = collect_cliques(1);
    printf("{\"edge_indices\":[%d,%d],\"edges\":[[%d,%d],[%d,%d]],\"zero_k5\":",
           first, second, edges[first].u, edges[first].v, edges[second].u, edges[second].v);
    print_clique_list(zeros);
    printf(",\"one_k5\":");
    print_clique_list(ones);
    printf(",\"total_burden\":%d}", zeros->count + ones->count);
    free(zeros);
    free(ones);
    toggle_edge(second);
    toggle_edge(first);
}

static int parse_index(const char *text) {
    char *end = NULL;
    errno = 0;
    long value = strtol(text, &end, 10);
    if (errno || end == text || *end != '\0' || value < 0 || value >= EDGE_COUNT) {
        fail("invalid edge index");
    }
    return (int)value;
}

int main(int argc, char **argv) {
    if (argc != 2 && argc != 5) {
        fprintf(stderr, "usage: %s MATRIX [--pair-indices FIRST SECOND]\n", argv[0]);
        return 2;
    }
    build_edges();
    parse_matrix(argv[1]);

    if (argc == 5) {
        if (strcmp(argv[2], "--pair-indices") != 0) {
            fail("unknown option");
        }
        int first = parse_index(argv[3]);
        int second = parse_index(argv[4]);
        if (first == second) {
            fail("pair indices must be distinct");
        }
        if (first > second) {
            int temporary = first;
            first = second;
            second = temporary;
        }
        printf("{\"checker\":\"c-fresh-recursive-enumeration\",\"record\":");
        print_record(first, second);
        printf("}\n");
        return 0;
    }

    uint32_t *scores = malloc(PAIR_COUNT * sizeof(*scores));
    if (scores == NULL) {
        fail("could not allocate pair ledger");
    }
    uint32_t minimum = UINT32_MAX;
    int cursor = 0;
    for (int first = 0; first < EDGE_COUNT; ++first) {
        for (int second = first + 1; second < EDGE_COUNT; ++second) {
            toggle_edge(first);
            toggle_edge(second);
            uint32_t score = count_all_violations();
            toggle_edge(second);
            toggle_edge(first);
            scores[cursor++] = score;
            if (score < minimum) {
                minimum = score;
            }
        }
    }
    if (cursor != PAIR_COUNT) {
        fail("pair-ledger cardinality mismatch");
    }

    printf("{\"checker\":\"c-fresh-recursive-enumeration\",\"order\":43,");
    printf("\"edge_order\":\"(u,v) lexicographic for 0 <= u < v < 43\",");
    printf("\"pair_order\":\"(first_edge_index,second_edge_index) lexicographic with first < second\",");
    printf("\"pair_count\":%d,\"minimum\":%u,\"scores\":[", PAIR_COUNT, minimum);
    for (int i = 0; i < PAIR_COUNT; ++i) {
        if (i) {
            putchar(',');
        }
        printf("%u", scores[i]);
    }
    printf("],\"minimizers\":[");
    cursor = 0;
    int printed = 0;
    for (int first = 0; first < EDGE_COUNT; ++first) {
        for (int second = first + 1; second < EDGE_COUNT; ++second) {
            if (scores[cursor] == minimum) {
                if (printed++) {
                    putchar(',');
                }
                print_record(first, second);
            }
            cursor += 1;
        }
    }
    printf("]}\n");
    free(scores);
    return 0;
}
