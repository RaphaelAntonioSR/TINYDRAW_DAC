# Demonstra a regra de sobreposição: o último desenho vence.
tela 24 por 12
cor VERMELHO = 255, 0, 0
cor AZUL     = 0, 0, 255

usar VERMELHO
retangulo em 2, 2 tamanho 10 por 7

usar AZUL
retangulo em 7, 4 tamanho 10 por 7     # cruza o vermelho; azul fica por cima
linha de 0, 0 ate 23, 0                # moldura superior
linha de 0, 11 ate 23, 11              # moldura inferior

salvar "sobreposicao.ppm"
