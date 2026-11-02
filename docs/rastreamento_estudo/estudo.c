/* Código gerado automaticamente pelo transpilador TinyDraw. */
/* Origem: estudo.td -- não edite manualmente. */
#include <stdio.h>
#include "tinydraw.h"

int main(void) {
    TDCanvas *c = td_criar(6, 4);
    if (!c) { fprintf(stderr, "erro: memoria insuficiente\n"); return 1; }
    printf("[linha 1] tela 6 por 4\n");
    /* linha 2 */
    int cor_1 = td_definir_cor(c, "VERMELHO", 255, 0, 0, 'V');
    printf("[linha 2] cor %s = (255, 0, 0) simbolo %c\n", "VERMELHO", 'V');
    /* linha 3 */
    int cor_2 = td_definir_cor(c, "AZUL", 0, 0, 255, 'A');
    printf("[linha 3] cor %s = (0, 0, 255) simbolo %c\n", "AZUL", 'A');
    /* linha 4 */
    td_usar(c, cor_1);
    printf("[linha 4] usar %s\n", "VERMELHO");
    /* linha 5 */
    td_retangulo(c, 1, 1, 4, 3);
    printf("[linha 5] retangulo em (1, 1) tamanho 4 x 3\n");
    /* linha 6 */
    td_linha(c, 0, 0, 5, 0);
    printf("[linha 6] linha (0, 0) -> (5, 0)\n");
    /* linha 7 */
    td_usar(c, cor_2);
    printf("[linha 7] usar %s\n", "AZUL");
    /* linha 8 */
    td_linha(c, 5, 0, 5, 3);
    printf("[linha 8] linha (5, 0) -> (5, 3)\n");
    /* linha 9 */
    td_ponto(c, 1, 1);
    printf("[linha 9] ponto em (1, 1)\n");
    /* linha 10 */
    if (td_salvar(c, "estudo.ppm") != 0) {
        td_liberar(c);
        return 1;
    }
    printf("[linha 10] salvar %s\n", "estudo.ppm");
    td_imprimir_ascii(c);
    td_liberar(c);
    return 0;
}
