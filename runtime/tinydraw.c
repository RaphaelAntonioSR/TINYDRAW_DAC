#include "tinydraw.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

TDCanvas *td_criar(int largura, int altura) {
    if (largura <= 0 || altura <= 0) return NULL;
    TDCanvas *c = (TDCanvas *)calloc(1, sizeof(TDCanvas));
    if (!c) return NULL;
    c->pixels = (unsigned char *)calloc((size_t)largura * (size_t)altura, 1);
    if (!c->pixels) { free(c); return NULL; }
    c->largura = largura;
    c->altura = altura;
    /* cor 0: fundo branco */
    strcpy(c->paleta[0].nome, "FUNDO");
    c->paleta[0].r = c->paleta[0].g = c->paleta[0].b = 255;
    c->paleta[0].simbolo = '.';
    c->ncores = 1;
    c->cor_ativa = 0;
    return c;
}

int td_definir_cor(TDCanvas *c, const char *nome, int r, int g, int b, char simbolo) {
    if (c->ncores >= TD_MAX_CORES) return -1;
    TDCor *k = &c->paleta[c->ncores];
    snprintf(k->nome, sizeof k->nome, "%s", nome);
    k->r = (unsigned char)r; k->g = (unsigned char)g; k->b = (unsigned char)b;
    k->simbolo = simbolo;
    return c->ncores++;
}

void td_usar(TDCanvas *c, int cor) {
    if (cor >= 0 && cor < c->ncores) c->cor_ativa = cor;
}

/* Regra de sobreposição: o último desenho sobrescreve os anteriores. */
void td_ponto(TDCanvas *c, int x, int y) {
    if (x < 0 || y < 0 || x >= c->largura || y >= c->altura) {
        fprintf(stderr, "aviso: pixel (%d, %d) fora da tela ignorado\n", x, y);
        return;
    }
    /* Matriz linear: avançar uma linha salta largura posições da paleta. */
    c->pixels[(size_t)y * c->largura + x] = (unsigned char)c->cor_ativa;
}

void td_linha(TDCanvas *c, int x1, int y1, int x2, int y2) {
    int i;
    if (y1 == y2) {
        int a = x1 < x2 ? x1 : x2, b = x1 < x2 ? x2 : x1;
        for (i = a; i <= b; i++) td_ponto(c, i, y1);
    } else if (x1 == x2) {
        int a = y1 < y2 ? y1 : y2, b = y1 < y2 ? y2 : y1;
        for (i = a; i <= b; i++) td_ponto(c, x1, i);
    } else {
        fprintf(stderr, "aviso: linha diagonal nao suportada\n");
    }
}

void td_retangulo(TDCanvas *c, int x, int y, int w, int h) {
    /* Dimensões contam pixels: largura 1 termina na própria coluna x. */
    int x2 = x + w - 1, y2 = y + h - 1;
    td_linha(c, x, y, x2, y);
    td_linha(c, x, y2, x2, y2);
    td_linha(c, x, y, x, y2);
    td_linha(c, x2, y, x2, y2);
}

int td_salvar(const TDCanvas *c, const char *arquivo) {
    FILE *f = fopen(arquivo, "wb");
    if (!f) { fprintf(stderr, "erro: nao foi possivel criar '%s'\n", arquivo); return 1; }
    fprintf(f, "P6\n%d %d\n255\n", c->largura, c->altura);
    size_t n = (size_t)c->largura * c->altura, i;
    for (i = 0; i < n; i++) {
        const TDCor *k = &c->paleta[c->pixels[i]];
        unsigned char rgb[3] = { k->r, k->g, k->b };
        if (fwrite(rgb, 1, 3, f) != 3) {
            fprintf(stderr, "erro: falha ao gravar pixels no PPM\n");
            fclose(f);
            return 1;
        }
    }
    /* fclose também pode detectar erro ao descarregar o buffer no disco. */
    if (ferror(f)) { fclose(f); return 1; }
    return fclose(f) == 0 ? 0 : 1;
}

void td_imprimir_ascii(const TDCanvas *c) {
    int x, y, i;
    printf("\nLegenda: '.' = fundo");
    for (i = 1; i < c->ncores; i++) printf(", '%c' = %s", c->paleta[i].simbolo, c->paleta[i].nome);
    printf("\n");
    if (c->largura > 120) { printf("(tela larga demais para exibir em ASCII; veja o arquivo PPM)\n"); return; }
    printf("+"); for (x = 0; x < c->largura; x++) putchar('-'); printf("+\n");
    for (y = 0; y < c->altura; y++) {
        putchar('|');
        for (x = 0; x < c->largura; x++)
            putchar(c->paleta[c->pixels[(size_t)y * c->largura + x]].simbolo);
        printf("|\n");
    }
    printf("+"); for (x = 0; x < c->largura; x++) putchar('-'); printf("+\n");
}

void td_liberar(TDCanvas *c) {
    if (!c) return;
    free(c->pixels);
    free(c);
}
