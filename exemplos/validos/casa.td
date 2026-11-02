# Casa com sol - exemplo completo de TinyDraw
tela 40 por 20

cor PAREDE  = 200, 120, 40
cor TELHADO = 255, 0, 0
cor PORTA   = 0, 0, 255
cor SOL     = 255, 200, 0

usar PAREDE
retangulo em 8, 9 tamanho 20 por 10

usar TELHADO
linha de 6, 8 ate 30, 8
linha de 8, 7 ate 28, 7
linha de 10, 6 ate 26, 6
linha de 12, 5 ate 24, 5
linha de 14, 4 ate 22, 4
linha de 16, 3 ate 20, 3
ponto em 18, 2

usar PORTA
retangulo em 16, 14 tamanho 4 por 5   # a porta sobrescreve a parede

usar SOL
retangulo em 34, 1 tamanho 3 por 3
ponto em 35, 2

salvar "casa.ppm"
