/* Independent R(5,5) checker: separate parsers plus recursive bitset cliques. */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_N 62

typedef struct {
    char *name;
    int n;
    uint64_t neighbor[MAX_N];
} Graph;

typedef struct {
    int (*sets)[5];
    size_t used;
    size_t capacity;
} Violations;

static void fail(const char *message) {
    fprintf(stderr, "checker_b: %s\n", message);
    exit(2);
}

static void fail_detail(const char *prefix, const char *detail) {
    fprintf(stderr, "checker_b: %s%s\n", prefix, detail);
    exit(2);
}

static void add_graph(Graph **graphs, size_t *used, size_t *capacity, Graph graph) {
    if (*used == *capacity) {
        size_t next = *capacity ? 2 * *capacity : 8;
        Graph *replacement = realloc(*graphs, next * sizeof(**graphs));
        if (!replacement) fail("out of memory while storing graphs");
        *graphs = replacement;
        *capacity = next;
    }
    (*graphs)[(*used)++] = graph;
}

static char *trim(char *line) {
    while (*line == ' ' || *line == '\t' || *line == '\r' || *line == '\n') ++line;
    char *end = line + strlen(line);
    while (end > line && (end[-1] == ' ' || end[-1] == '\t' || end[-1] == '\r' || end[-1] == '\n')) --end;
    *end = '\0';
    return line;
}

static Graph *parse_matrices(const char *path, size_t *count) {
    FILE *file = fopen(path, "rb");
    if (!file) fail_detail("cannot open input: ", strerror(errno));
    Graph *graphs = NULL;
    size_t used = 0, capacity = 0, rows_used = 0, rows_capacity = 0;
    char **rows = NULL;
    char *current_name = NULL;
    char *buffer = NULL;
    size_t buffer_size = 0;

    while (getline(&buffer, &buffer_size, file) >= 0) {
        char *line = trim(buffer);
        if (!*line || *line == '#') continue;
        if (line[0] == '>' && line[1] == ' ') {
            if (current_name) {
                if (rows_used < 1 || rows_used > MAX_N) fail("matrix order outside 1..62");
                Graph graph = {.name = current_name, .n = (int)rows_used, .neighbor = {0}};
                for (size_t i = 0; i < rows_used; ++i) {
                    if (strlen(rows[i]) != rows_used) fail("matrix is not square");
                    for (size_t j = 0; j < rows_used; ++j) {
                        if (rows[i][j] != '0' && rows[i][j] != '1') fail("matrix has a non-binary character");
                        if (i == j && rows[i][j] != '0') fail("matrix contains a loop");
                        if (rows[i][j] != rows[j][i]) fail("matrix is asymmetric");
                        if (rows[i][j] == '1') graph.neighbor[i] |= UINT64_C(1) << j;
                    }
                }
                for (size_t i = 0; i < rows_used; ++i) free(rows[i]);
                rows_used = 0;
                add_graph(&graphs, &used, &capacity, graph);
            }
            current_name = strdup(trim(line + 2));
            if (!current_name || !*current_name) fail("empty graph name");
            for (size_t i = 0; i < used; ++i) {
                if (!strcmp(graphs[i].name, current_name)) fail("duplicate graph name");
            }
        } else {
            if (!current_name) fail("matrix row before graph header");
            if (rows_used == rows_capacity) {
                size_t next = rows_capacity ? 2 * rows_capacity : 64;
                char **replacement = realloc(rows, next * sizeof(*rows));
                if (!replacement) fail("out of memory while storing matrix rows");
                rows = replacement;
                rows_capacity = next;
            }
            rows[rows_used] = strdup(line);
            if (!rows[rows_used]) fail("out of memory while copying matrix row");
            ++rows_used;
        }
    }
    free(buffer);
    if (ferror(file)) fail("read failure");
    fclose(file);
    if (!current_name) fail("no named matrices found");
    if (rows_used < 1 || rows_used > MAX_N) fail("matrix order outside 1..62");
    Graph graph = {.name = current_name, .n = (int)rows_used, .neighbor = {0}};
    for (size_t i = 0; i < rows_used; ++i) {
        if (strlen(rows[i]) != rows_used) fail("matrix is not square");
        for (size_t j = 0; j < rows_used; ++j) {
            if (rows[i][j] != '0' && rows[i][j] != '1') fail("matrix has a non-binary character");
            if (i == j && rows[i][j] != '0') fail("matrix contains a loop");
            if (rows[i][j] != rows[j][i]) fail("matrix is asymmetric");
            if (rows[i][j] == '1') graph.neighbor[i] |= UINT64_C(1) << j;
        }
    }
    for (size_t i = 0; i < rows_used; ++i) free(rows[i]);
    free(rows);
    add_graph(&graphs, &used, &capacity, graph);
    *count = used;
    return graphs;
}

static Graph *parse_graph6(const char *path, size_t *count) {
    FILE *file = fopen(path, "rb");
    if (!file) fail_detail("cannot open input: ", strerror(errno));
    Graph *graphs = NULL;
    size_t used = 0, capacity = 0;
    char *buffer = NULL;
    size_t buffer_size = 0;
    ssize_t length;
    while ((length = getline(&buffer, &buffer_size, file)) >= 0) {
        while (length > 0 && (buffer[length - 1] == '\n' || buffer[length - 1] == '\r')) --length;
        if (length == 0) fail("blank graph6 record");
        for (ssize_t i = 0; i < length; ++i) {
            unsigned char ch = (unsigned char)buffer[i];
            if (ch < 63 || ch > 126) fail("invalid graph6 character");
        }
        if ((unsigned char)buffer[0] == 126) fail("only short graph6 n<=62 is supported");
        int n = (unsigned char)buffer[0] - 63;
        int edge_bits = n * (n - 1) / 2;
        int encoded = (edge_bits + 5) / 6;
        if (length != 1 + encoded) fail("wrong graph6 record length");
        Graph graph = {.name = NULL, .n = n, .neighbor = {0}};
        char name[32];
        snprintf(name, sizeof(name), "g6_%04zu", used + 1);
        graph.name = strdup(name);
        if (!graph.name) fail("out of memory while naming graph6 record");
        int cursor = 0;
        for (int high = 1; high < n; ++high) {
            for (int low = 0; low < high; ++low) {
                int group = cursor / 6;
                int offset = cursor % 6;
                int value = (unsigned char)buffer[1 + group] - 63;
                if ((value >> (5 - offset)) & 1) {
                    graph.neighbor[low] |= UINT64_C(1) << high;
                    graph.neighbor[high] |= UINT64_C(1) << low;
                }
                ++cursor;
            }
        }
        for (int bit = cursor; bit < encoded * 6; ++bit) {
            int group = bit / 6, offset = bit % 6;
            int value = (unsigned char)buffer[1 + group] - 63;
            if ((value >> (5 - offset)) & 1) fail("nonzero graph6 padding bit");
        }
        add_graph(&graphs, &used, &capacity, graph);
    }
    free(buffer);
    if (ferror(file)) fail("read failure");
    fclose(file);
    if (!used) fail("empty graph6 file");
    *count = used;
    return graphs;
}

static void append_violation(Violations *violations, const int stack[5]) {
    if (violations->used == violations->capacity) {
        size_t next = violations->capacity ? 2 * violations->capacity : 8;
        int (*replacement)[5] = realloc(violations->sets, next * sizeof(*violations->sets));
        if (!replacement) fail("out of memory while storing violations");
        violations->sets = replacement;
        violations->capacity = next;
    }
    memcpy(violations->sets[violations->used++], stack, 5 * sizeof(int));
}

static void enumerate_cliques(const uint64_t neighbor[MAX_N], uint64_t candidates,
                              int depth, int stack[5], Violations *violations) {
    if (depth == 5) {
        append_violation(violations, stack);
        return;
    }
    if (__builtin_popcountll(candidates) < 5 - depth) return;
    while (candidates) {
        int vertex = __builtin_ctzll(candidates);
        candidates &= candidates - 1;
        stack[depth] = vertex;
        enumerate_cliques(neighbor, candidates & neighbor[vertex], depth + 1, stack, violations);
    }
}

static void force_first_five(Graph *graph, bool value) {
    if (graph->n < 5) fail("force control needs at least 5 vertices");
    for (int i = 0; i < 5; ++i) {
        for (int j = 0; j < i; ++j) {
            if (value) {
                graph->neighbor[i] |= UINT64_C(1) << j;
                graph->neighbor[j] |= UINT64_C(1) << i;
            } else {
                graph->neighbor[i] &= ~(UINT64_C(1) << j);
                graph->neighbor[j] &= ~(UINT64_C(1) << i);
            }
        }
    }
}

static void delete_vertex(Graph *graph, int vertex) {
    if (vertex < 0 || vertex >= graph->n) fail("delete vertex outside graph order");
    uint64_t next[MAX_N] = {0};
    int new_n = graph->n - 1;
    for (int old_i = 0; old_i < graph->n; ++old_i) {
        if (old_i == vertex) continue;
        int new_i = old_i - (old_i > vertex);
        for (int old_j = 0; old_j < graph->n; ++old_j) {
            if (old_j == vertex) continue;
            if ((graph->neighbor[old_i] >> old_j) & 1) {
                int new_j = old_j - (old_j > vertex);
                next[new_i] |= UINT64_C(1) << new_j;
            }
        }
    }
    memcpy(graph->neighbor, next, sizeof(next));
    graph->n = new_n;
}

static void print_string(const char *text) {
    putchar('"');
    for (; *text; ++text) {
        if (*text == '"' || *text == '\\') putchar('\\');
        putchar(*text);
    }
    putchar('"');
}

static void print_sets(const Violations *violations) {
    putchar('[');
    for (size_t i = 0; i < violations->used; ++i) {
        if (i) putchar(',');
        printf("[%d,%d,%d,%d,%d]", violations->sets[i][0], violations->sets[i][1],
               violations->sets[i][2], violations->sets[i][3], violations->sets[i][4]);
    }
    putchar(']');
}

static void print_checked_graph(Graph *graph) {
    uint64_t all = graph->n == 64 ? UINT64_MAX : ((UINT64_C(1) << graph->n) - 1);
    uint64_t complement[MAX_N] = {0};
    long edges = 0;
    for (int i = 0; i < graph->n; ++i) {
        graph->neighbor[i] &= all & ~(UINT64_C(1) << i);
        complement[i] = all & ~(UINT64_C(1) << i) & ~graph->neighbor[i];
        edges += __builtin_popcountll(graph->neighbor[i]);
    }
    int stack[5] = {0};
    Violations zero = {0}, one = {0};
    enumerate_cliques(complement, all, 0, stack, &zero);
    enumerate_cliques(graph->neighbor, all, 0, stack, &one);

    printf("{\"degrees\":[");
    for (int i = 0; i < graph->n; ++i) {
        if (i) putchar(',');
        printf("%d", __builtin_popcountll(graph->neighbor[i]));
    }
    printf("],\"edges\":%ld,\"id\":", edges / 2);
    print_string(graph->name);
    printf(",\"n\":%d,\"one_k5\":", graph->n);
    print_sets(&one);
    printf(",\"zero_k5\":");
    print_sets(&zero);
    putchar('}');
    free(zero.sets);
    free(one.sets);
}

int main(int argc, char **argv) {
    const char *format = NULL, *path = NULL, *selected = NULL, *force = NULL;
    int deletion = -1;
    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--format") && i + 1 < argc) format = argv[++i];
        else if (!strcmp(argv[i], "--input") && i + 1 < argc) path = argv[++i];
        else if (!strcmp(argv[i], "--id") && i + 1 < argc) selected = argv[++i];
        else if (!strcmp(argv[i], "--force") && i + 1 < argc) force = argv[++i];
        else if (!strcmp(argv[i], "--delete") && i + 1 < argc) deletion = atoi(argv[++i]);
        else fail("invalid command line");
    }
    if (!format || !path) fail("--format and --input are required");
    if (force && deletion >= 0) fail("--force and --delete are mutually exclusive");
    size_t count = 0;
    Graph *graphs = !strcmp(format, "matrix") ? parse_matrices(path, &count)
                   : !strcmp(format, "graph6") ? parse_graph6(path, &count)
                   : (fail("format must be matrix or graph6"), NULL);

    printf("{\"checker\":\"B-recursive-bitsets\",\"graphs\":[");
    size_t emitted = 0;
    for (size_t i = 0; i < count; ++i) {
        if (selected && strcmp(selected, graphs[i].name)) continue;
        if (force) {
            if (!strcmp(force, "clique")) force_first_five(&graphs[i], true);
            else if (!strcmp(force, "independent")) force_first_five(&graphs[i], false);
            else fail("force must be clique or independent");
            size_t length = strlen(graphs[i].name) + strlen(force) + 9;
            char *renamed = malloc(length);
            if (!renamed) fail("out of memory while renaming forced graph");
            snprintf(renamed, length, "%s_forced_%s", graphs[i].name, force);
            free(graphs[i].name);
            graphs[i].name = renamed;
        }
        if (deletion >= 0) {
            delete_vertex(&graphs[i], deletion);
            char suffix[40];
            snprintf(suffix, sizeof(suffix), "_deleted_%d", deletion);
            size_t length = strlen(graphs[i].name) + strlen(suffix) + 1;
            char *renamed = malloc(length);
            if (!renamed) fail("out of memory while renaming deleted graph");
            snprintf(renamed, length, "%s%s", graphs[i].name, suffix);
            free(graphs[i].name);
            graphs[i].name = renamed;
        }
        if (emitted++) putchar(',');
        print_checked_graph(&graphs[i]);
    }
    printf("]}\n");
    if (selected && emitted != 1) fail("selected graph id not found exactly once");
    for (size_t i = 0; i < count; ++i) free(graphs[i].name);
    free(graphs);
    return 0;
}
