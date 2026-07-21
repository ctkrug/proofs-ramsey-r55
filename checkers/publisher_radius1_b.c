/* Direct raw Springer-matrix parser and independent recursive-bitset checker. */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ORDER 43
#define TITLE "# Supplementary Data 4: The coloring matrix with only 2 monochromatic 5-cliques of a complete graph with 43 nodes"

typedef struct {
    int (*sets)[5];
    size_t used;
    size_t capacity;
} Violations;

static void fail(const char *message) {
    fprintf(stderr, "publisher_radius1_b: %s\n", message);
    exit(2);
}

static void fail_errno(const char *message) {
    fprintf(stderr, "publisher_radius1_b: %s: %s\n", message, strerror(errno));
    exit(2);
}

static void strip_line_end(char *line, ssize_t *length) {
    if (*length > 0 && line[*length - 1] == '\n') line[--*length] = '\0';
    if (*length > 0 && line[*length - 1] == '\r') fail("CR is not admitted in the frozen publisher body");
}

static void parse_raw(const char *path, uint64_t neighbor[ORDER]) {
    FILE *file = fopen(path, "rb");
    if (!file) fail_errno("cannot open input");
    char *line = NULL;
    size_t capacity = 0;
    ssize_t length = getline(&line, &capacity, file);
    if (length < 0) fail("empty input");
    strip_line_end(line, &length);
    if (strcmp(line, TITLE)) fail("publisher title line mismatch");

    int matrix[ORDER][ORDER] = {{0}};
    for (int i = 0; i < ORDER; ++i) {
        length = getline(&line, &capacity, file);
        if (length < 0) fail("short publisher matrix");
        strip_line_end(line, &length);
        if (length != 2 * ORDER - 1) fail("row does not have the exact frozen width");
        for (int j = 0; j < ORDER; ++j) {
            int position = 2 * j;
            if (line[position] != '0' && line[position] != '1') fail("nonbinary publisher token");
            if (j + 1 < ORDER && line[position + 1] != ' ') fail("publisher token separator is not one space");
            matrix[i][j] = line[position] - '0';
        }
    }
    if (getline(&line, &capacity, file) >= 0) fail("extra line after publisher matrix");
    if (ferror(file)) fail_errno("read failure");
    free(line);
    fclose(file);

    for (int i = 0; i < ORDER; ++i) {
        if (matrix[i][i]) fail("nonzero diagonal");
        for (int j = 0; j < i; ++j) {
            if (matrix[i][j] != matrix[j][i]) fail("asymmetric publisher matrix");
        }
        neighbor[i] = 0;
        for (int j = 0; j < ORDER; ++j) {
            if (matrix[i][j]) neighbor[i] |= UINT64_C(1) << j;
        }
    }
}

static void append(Violations *violations, const int stack[5]) {
    if (violations->used == violations->capacity) {
        size_t next = violations->capacity ? 2 * violations->capacity : 8;
        int (*replacement)[5] = realloc(violations->sets, next * sizeof(*violations->sets));
        if (!replacement) fail("out of memory");
        violations->sets = replacement;
        violations->capacity = next;
    }
    memcpy(violations->sets[violations->used++], stack, 5 * sizeof(int));
}

static void enumerate_cliques(const uint64_t neighbor[ORDER], uint64_t candidates,
                              int depth, int stack[5], Violations *violations) {
    if (depth == 5) {
        append(violations, stack);
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

static void compute(const uint64_t neighbor[ORDER], Violations *zero, Violations *one) {
    uint64_t all = (UINT64_C(1) << ORDER) - 1;
    uint64_t complement[ORDER] = {0};
    for (int i = 0; i < ORDER; ++i) {
        complement[i] = all & ~(UINT64_C(1) << i) & ~neighbor[i];
    }
    int stack[5] = {0};
    enumerate_cliques(complement, all, 0, stack, zero);
    enumerate_cliques(neighbor, all, 0, stack, one);
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

static void print_result(const uint64_t neighbor[ORDER]) {
    Violations zero = {0}, one = {0};
    compute(neighbor, &zero, &one);
    printf("{\"one_k5\":");
    print_sets(&one);
    printf(",\"zero_k5\":");
    print_sets(&zero);
    putchar('}');
    free(zero.sets);
    free(one.sets);
}

int main(int argc, char **argv) {
    const char *path = NULL;
    bool seed_only = false;
    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--input") && i + 1 < argc) path = argv[++i];
        else if (!strcmp(argv[i], "--seed-only")) seed_only = true;
        else fail("usage: publisher_radius1_b --input PATH [--seed-only]");
    }
    if (!path) fail("--input is required");
    uint64_t neighbor[ORDER] = {0};
    parse_raw(path, neighbor);

    long edge_count = 0;
    for (int i = 0; i < ORDER; ++i) edge_count += __builtin_popcountll(neighbor[i]);
    printf("{\"checker\":\"B-per-flip-recursive-bitset-cliques\",\"seed\":");
    print_result(neighbor);
    printf(",\"source\":{\"edges\":%ld,\"n\":%d,\"upper_triangle_bits\":\"", edge_count / 2, ORDER);
    for (int high = 1; high < ORDER; ++high) {
        for (int low = 0; low < high; ++low) {
            putchar((neighbor[low] & (UINT64_C(1) << high)) ? '1' : '0');
        }
    }
    printf("\"}");
    if (!seed_only) {
        printf(",\"radius1\":[");
        bool first = true;
        for (int u = 0; u < ORDER; ++u) {
            for (int v = u + 1; v < ORDER; ++v) {
                if (!first) putchar(',');
                first = false;
                int original = (neighbor[u] >> v) & 1;
                neighbor[u] ^= UINT64_C(1) << v;
                neighbor[v] ^= UINT64_C(1) << u;
                printf("{\"edge\":[%d,%d],\"original\":%d,", u, v, original);
                Violations zero = {0}, one = {0};
                compute(neighbor, &zero, &one);
                printf("\"one_k5\":");
                print_sets(&one);
                printf(",\"zero_k5\":");
                print_sets(&zero);
                putchar('}');
                free(zero.sets);
                free(one.sets);
                neighbor[u] ^= UINT64_C(1) << v;
                neighbor[v] ^= UINT64_C(1) << u;
            }
        }
        putchar(']');
    }
    printf("}\n");
    return 0;
}
