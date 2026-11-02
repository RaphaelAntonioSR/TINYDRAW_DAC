/* Biblioteca auxiliar de execução da TinyDraw.
 * O código gerado pelo transpilador fornece os dados e comandos;
 * esta biblioteca apenas mantém a matriz de pixels e grava o PPM. */
#ifndef TINYDRAW_H
#define TINYDRAW_H

#define TD_MAX_CORES 256   /* índice 0 = fundo branco */

typedef struct {
    char nome[64];
    unsigned char r, g, b;
    char simbolo;          /* caractere usado na visualização ASCII */
} TDCor;

typedef struct {
    int largura, altura;
    unsigned char *pixels; /* índices da paleta, linha a linha (origem no canto superior esquerdo) */
    TDCor paleta[TD_MAX_CORES];
    int ncores;
    int cor_ativa;
} TDCanvas;

TDCanvas *td_criar(int largura, int altura);
int  td_definir_cor(TDCanvas *c, const char *nome, int r, int g, int b, char simbolo);
void td_usar(TDCanvas *c, int cor);
void td_ponto(TDCanvas *c, int x, int y);
void td_linha(TDCanvas *c, int x1, int y1, int x2, int y2);   /* horizontal ou vertical */
void td_retangulo(TDCanvas *c, int x, int y, int largura, int altura); /* só contorno */
int  td_salvar(const TDCanvas *c, const char *arquivo);        /* 0 = sucesso */
void td_imprimir_ascii(const TDCanvas *c);
void td_liberar(TDCanvas *c);

#endif
