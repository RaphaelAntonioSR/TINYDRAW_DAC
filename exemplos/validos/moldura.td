# Molduras concêntricas, com sinônimos acentuados (retângulo / até).
tela 30 por 15
cor LARANJA = 255, 140, 0
cor VERDE   = 0, 160, 0
cor ROXO    = 120, 0, 160

usar LARANJA
retângulo em 0, 0 tamanho 30 por 15
usar VERDE
retangulo em 2, 2 tamanho 26 por 11
usar ROXO
retangulo em 4, 4 tamanho 22 por 7
linha de 15, 4 até 15, 10
linha de 4, 7 ate 25, 7

salvar "moldura.ppm"
