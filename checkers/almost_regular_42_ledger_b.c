#include <stdio.h>
#include <stdlib.h>

static int edge_variable(int u, int v) {
    int low = u < v ? u : v;
    int high = u < v ? v : u;
    if (low == high) {
        fprintf(stderr, "loop passed to edge_variable\n");
        exit(2);
    }
    return high * (high - 1) / 2 + low + 1;
}

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: %s ORDER CLIQUE_SIZE LEDGER\n", argv[0]);
        return 2;
    }
    int n = atoi(argv[1]), k = atoi(argv[2]);
    if (n < 1 || k < 2 || k > n || k > 5) {
        fprintf(stderr, "unsupported order or clique size\n");
        return 2;
    }
    FILE *output = fopen(argv[3], "wb");
    if (!output) {
        perror("ledger");
        return 2;
    }
    int v[5] = {0, 0, 0, 0, 0};
    unsigned long long five_sets = 0;
    if (k == 3) {
        for (v[0] = 0; v[0] < n; ++v[0])
        for (v[1] = v[0] + 1; v[1] < n; ++v[1])
        for (v[2] = v[1] + 1; v[2] < n; ++v[2]) {
            for (int color = 0; color < 2; ++color) {
                for (int i = 0; i < 3; ++i) for (int j = i + 1; j < 3; ++j) {
                    int variable = edge_variable(v[i], v[j]);
                    fprintf(output, "%d ", color ? -variable : variable);
                }
                fputs("0\n", output);
            }
            ++five_sets;
        }
    } else if (k == 5) {
        for (v[0] = 0; v[0] < n; ++v[0])
        for (v[1] = v[0] + 1; v[1] < n; ++v[1])
        for (v[2] = v[1] + 1; v[2] < n; ++v[2])
        for (v[3] = v[2] + 1; v[3] < n; ++v[3])
        for (v[4] = v[3] + 1; v[4] < n; ++v[4]) {
            for (int color = 0; color < 2; ++color) {
                for (int i = 0; i < 5; ++i) for (int j = i + 1; j < 5; ++j) {
                    int variable = edge_variable(v[i], v[j]);
                    fprintf(output, "%d ", color ? -variable : variable);
                }
                fputs("0\n", output);
            }
            ++five_sets;
        }
    } else {
        fprintf(stderr, "only clique sizes 3 and 5 are implemented independently\n");
        fclose(output);
        return 2;
    }
    if (fclose(output)) {
        perror("close ledger");
        return 2;
    }
    fprintf(stderr, "sets=%llu clauses=%llu\n", five_sets, 2 * five_sets);
    return 0;
}
