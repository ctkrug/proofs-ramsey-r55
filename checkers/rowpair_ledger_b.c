/* Independent C/bitset graph6 parser and adjacency-row ledger producer. */
#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int a, b, epsilon, common, common_non, distance, count;
} Type;

static int compare_type(const void *left, const void *right) {
    const Type *x = left, *y = right;
    if (x->a != y->a) return x->a - y->a;
    if (x->b != y->b) return x->b - y->b;
    if (x->epsilon != y->epsilon) return x->epsilon - y->epsilon;
    if (x->common != y->common) return x->common - y->common;
    if (x->common_non != y->common_non) return x->common_non - y->common_non;
    return x->distance - y->distance;
}

static int parse_graph6(const char *text, uint64_t rows[63]) {
    size_t length = strlen(text);
    while (length && (text[length - 1] == '\n' || text[length - 1] == '\r')) length--;
    if (!length) return -1;
    int n = (unsigned char)text[0] - 63;
    if (n < 0 || n > 62) return -1;
    size_t need = 1 + ((size_t)n * (n - 1) / 2 + 5) / 6;
    if (length != need) return -1;
    for (int i = 0; i < n; ++i) rows[i] = 0;
    size_t bit = 0;
    for (int j = 1; j < n; ++j) {
        for (int i = 0; i < j; ++i, ++bit) {
            int value = (unsigned char)text[1 + bit / 6] - 63;
            if (value < 0 || value >= 64) return -1;
            if ((value >> (5 - bit % 6)) & 1) {
                rows[i] |= UINT64_C(1) << j;
                rows[j] |= UINT64_C(1) << i;
            }
        }
    }
    return n;
}

static int emit_graph(FILE *out, int index, char variant, const uint64_t rows[63], int n) {
    int degrees[63];
    Type types[3906];
    int type_count = 0;
    for (int i = 0; i < n; ++i) degrees[i] = __builtin_popcountll(rows[i]);
    fprintf(out, "G\t%03d\t%c\t", index, variant);
    for (int i = 0; i < n; ++i) fprintf(out, "%s%d", i ? "," : "", degrees[i]);
    fputc('\n', out);
    for (int u = 0; u < n; ++u) {
        for (int v = 0; v < n; ++v) {
            if (u == v) continue;
            int epsilon = (int)((rows[u] >> v) & 1U);
            int common = __builtin_popcountll(rows[u] & rows[v]);
            int common_non = n - 2 - degrees[u] - degrees[v] + 2 * epsilon + common;
            int distance = degrees[u] + degrees[v] - 2 * common;
            types[type_count++] = (Type){degrees[u], degrees[v], epsilon, common,
                                       common_non, distance, 1};
        }
    }
    qsort(types, (size_t)type_count, sizeof(Type), compare_type);
    for (int start = 0; start < type_count;) {
        int end = start + 1;
        while (end < type_count && compare_type(&types[start], &types[end]) == 0) end++;
        Type *x = &types[start];
        fprintf(out, "T\t%03d\t%c\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n",
                index, variant, x->a, x->b, x->epsilon, x->common,
                x->common_non, x->distance, end - start);
        start = end;
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: %s INPUT.g6 OUTPUT.tsv\n", argv[0]);
        return 2;
    }
    FILE *in = fopen(argv[1], "rb"), *out = fopen(argv[2], "wb");
    if (!in || !out) {
        fprintf(stderr, "open failed: %s\n", strerror(errno));
        return 2;
    }
    fputs("rowpair-ledger-v1\n", out);
    char line[256];
    int index = 0;
    while (fgets(line, sizeof(line), in)) {
        uint64_t rows[63], comp[63];
        int n = parse_graph6(line, rows);
        if (n < 0) {
            fprintf(stderr, "invalid graph6 record %d\n", index);
            return 1;
        }
        emit_graph(out, index, 'O', rows, n);
        uint64_t mask = n == 64 ? UINT64_MAX : ((UINT64_C(1) << n) - 1);
        for (int i = 0; i < n; ++i) comp[i] = (~rows[i]) & mask & ~(UINT64_C(1) << i);
        emit_graph(out, index, 'C', comp, n);
        index++;
    }
    if (ferror(in) || fclose(in) || fclose(out)) return 2;
    return 0;
}
