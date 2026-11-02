# TinyDraw — Documentação do Projeto

**Curso:** Engenharia de Computação — 8º semestre
**Disciplina/DAC:** Compiladores (Análise Léxica, Sintática e Semântica) — Desafio de Articulação de Competências
**Professor:** Gabriel Toshio Hirokawa Higa
**Equipe:** Antonio Marcos dos Santos Junior · Fernando Augusto da Silva · Raphael Antonio dos Santos Rangel
**Proposta escolhida:** 8 — TinyDraw: desenhos simples em imagem ou texto

---

## 1. Problema, usuário, propósito, limites e resultado esperado

**Problema.** Gerar uma imagem simples (pontos, linhas, retângulos coloridos) em C exige alocar matriz de pixels,
controlar índices, escrever o formato de arquivo e tratar limites — detalhes que desviam a atenção de *o que* se quer desenhar.

**Usuário.** Estudante ou iniciante que quer descrever figuras geométricas simples de forma declarativa, em português.

**Propósito.** A TinyDraw permite escrever o desenho como uma sequência curta de comandos legíveis. O transpilador
valida o programa e gera C que produz um arquivo de imagem **PPM** e uma visualização **ASCII**.

**Modelagem computacional.** O desenho é uma máquina de estado: uma *tela* (matriz W×H de índices de paleta),
uma *paleta* (cores nomeadas) e uma *cor ativa*. Cada comando de desenho altera a matriz usando a cor ativa.
Justifica-se uma DSL porque o domínio é pequeno e fechado, e a maior parte dos erros (coordenada fora da tela,
cor inexistente, componente > 255) é detectável **estaticamente**, antes de executar qualquer C.

**Limites.** Sem preenchimento, sem diagonais, sem círculos, sem repetição/variáveis, sem antialiasing,
sem biblioteca gráfica no runtime C. O Studio é uma extensão com editor de texto. Tela de no máximo 1000×1000 e até 255 cores.

**Resultado esperado.** Para um programa válido: arquivo `.c`, executável, `.ppm` correto e desenho em ASCII.
Para um programa inválido: diagnósticos com arquivo:linha:coluna e **nenhum** código gerado.

## 2. A linguagem

### 2.1 Visão geral
```
tela 40 por 20                          # declara a tela (obrigatório, uma vez, antes de desenhar)
cor VERMELHO = 255, 0, 0                # declara uma cor nomeada (R, G, B)
usar VERMELHO                           # seleciona a cor ativa
ponto em 10, 10                         # um pixel
linha de 2, 2 ate 30, 2                 # linha horizontal ou vertical
retangulo em 5, 5 tamanho 12 por 8      # contorno de retângulo
salvar "desenho.ppm"                    # grava o arquivo (obrigatório, uma vez, por último)
```

### 2.2 Decisões de projeto
| Tema | Decisão |
|---|---|
| Sistema de coordenadas | Origem `(0,0)` no **canto superior esquerdo**; `x` cresce para a direita e `y` para baixo. Válido: `0 ≤ x < largura`, `0 ≤ y < altura`. |
| Fundo | Branco (255,255,255), símbolo `.` no ASCII. |
| Sobreposição | **O último desenho sobrescreve os anteriores** (pintor). |
| Retângulo | Só contorno; `(x, y)` é o canto superior esquerdo; ocupa `x..x+largura-1` e `y..y+altura-1`. |
| Linha | Horizontal (`y1 = y2`) ou vertical (`x1 = x2`); extremos incluídos; a ordem dos extremos é livre. |
| Fora dos limites | **Erro** semântico (não há recorte silencioso). |
| Palavras reservadas | Em português, minúsculas (*case-sensitive*). `retângulo` e `até` também são aceitos como sinônimos de `retangulo` e `ate`. |
| Comentários | De `#` até o fim da linha. |
| Espaços/quebras de linha | Irrelevantes para a sintaxe (cada comando começa por palavra reservada). |

## 3. Especificação léxica (expressões regulares)

Um *scanner* baseado em uma única regex com grupos nomeados; a primeira alternativa que casar vence (ordem abaixo).

| Token | Expressão regular | Observação |
|---|---|---|
| `COMENTARIO` | `#[^\n]*` | descartado |
| `ESPACO` | `[ \t\r]+` | descartado |
| `NOVA_LINHA` | `\n` | descartado (conta linhas) |
| `STRING` | `"[^"\n]*"` | nome de arquivo |
| `STRING_ABERTA` | `"[^\n]*` | **erro léxico**: string não terminada |
| `INT` | `[0-9]+` | inteiro sem sinal |
| `ID` | `[^\W\d]\w*` | letra ou `_`, seguida de letras/dígitos/`_` (aceita acentos) |
| `VIRGULA` | `,` | |
| `IGUAL` | `=` | |
| `DESCONHECIDO` | `.` | **erro léxico**: caractere inesperado |

**Palavras reservadas** (reclassificadas a partir de `ID`; viram tokens de mesmo nome em maiúsculas):

| Palavra | Token | Uso |
|---|---|---|
| `tela` | TELA | declara dimensões |
| `cor` | COR | define cor nomeada |
| `usar` | USAR | seleciona cor |
| `ponto` | PONTO | desenha pixel |
| `linha` | LINHA | desenha linha |
| `retangulo` / `retângulo` | RETANGULO | desenha contorno |
| `salvar` | SALVAR | grava o arquivo |
| `em`, `de`, `ate` / `até`, `tamanho`, `por` | EM, DE, ATE, TAMANHO, POR | palavras de ligação |

Observações: números negativos **não** existem na linguagem (`-` é erro léxico); `TELA` em maiúsculas é um `ID`, não a palavra reservada.
Os erros léxicos são coletados todos de uma vez e interrompem a compilação antes do parser.

## 4. Especificação sintática (EBNF)

```ebnf
programa    = { comando } EOF ;

comando     = tela | cor | usar | ponto | linha | retangulo | salvar ;

tela        = "tela" INT "por" INT ;
cor         = "cor" ID "=" INT "," INT "," INT ;
usar        = "usar" ID ;
ponto       = "ponto" "em" par ;
linha       = "linha" "de" par "ate" par ;
retangulo   = "retangulo" "em" par "tamanho" INT "por" INT ;
salvar      = "salvar" STRING ;

par         = INT "," INT ;
```

A gramática é **LL(1)**: cada `comando` começa por uma palavra reservada distinta, então o analisador descendente
recursivo escolhe a regra olhando apenas o token atual, sem retrocesso nem recursão à esquerda.
Após o primeiro erro sintático a análise é interrompida, com mensagem do tipo
`esperado 'por', encontrado 'salvar'` e posição linha:coluna.

## 5. Regras semânticas

A análise semântica percorre a AST em ordem, mantendo: **tabela de símbolos** (cores: nome, RGB, linha de declaração,
índice na paleta, flag *usada*), a **dimensão** da tela e a **cor ativa**.

| # | Regra | Severidade |
|---|---|---|
| S1 | Deve existir exatamente uma `tela`; segunda declaração é erro | erro |
| S2 | Comandos (`ponto`, `linha`, `retangulo`, `salvar`) só após a `tela` | erro |
| S3 | `largura` e `altura` da tela positivas e ≤ 1000 | erro |
| S4 | Nome de cor não pode ser repetido | erro |
| S5 | Componentes R, G, B entre 0 e 255 | erro |
| S6 | No máximo 255 cores | erro |
| S7 | `usar` exige cor previamente declarada | erro |
| S8 | Desenhar exige uma cor ativa (`usar` antes) | erro |
| S9 | Pontos/extremos de linha e canto de retângulo dentro da tela | erro |
| S10 | Linha deve ser horizontal ou vertical | erro |
| S11 | Retângulo com largura e altura positivas e inteiramente dentro da tela | erro |
| S12 | `salvar` com nome não vazio, extensão `.ppm`, **sem pastas** (`/`, `\`, `:`) e sem caracteres/nomes reservados incompatíveis com Windows | erro |
| S13 | Exatamente um `salvar`, e nenhum comando depois dele | erro |
| S14 | Cor declarada mas nunca usada | aviso |
| S15 | Linha degenerada (início = fim) | aviso |

Erros semânticos são acumulados e exibidos todos juntos, ordenados por posição. Havendo ao menos um erro **nenhum C é gerado**.
Avisos não impedem a geração.

## 6. Arquitetura e engenharia de software

```
texto .td ──► lexer.py ──► tokens ──► parser.py ──► AST ──► semantica.py ──► AST + tabela ──► codegen.py ──► .c
                │ erros léxicos          │ erro sintático          │ erros/avisos semânticos
                └────────────── Diagnostico (erros.py) ────────────┘          compilador.py orquestra
                                                                              cli.py: gcc + execução
```

| Módulo | Responsabilidade |
|---|---|
| `lexer.py` | Especificação léxica (regex), `Token`, diagnósticos léxicos |
| `ast_nodes.py` | Nós da AST (`dataclass`) e impressão da árvore |
| `parser.py` | Descendente recursivo LL(1) |
| `semantica.py` | `TabelaDeSimbolos` e `Analisador` (regras S1–S15) |
| `codegen.py` | Gera C; atribui um símbolo ASCII por cor |
| `compilador.py` | `transpilar(texto) -> Resultado` (interface usada pela CLI e pelos testes) |
| `cli.py` / `__main__.py` | Linha de comando, chamada ao `gcc`, execução |
| `runtime/tinydraw.[ch]` | Biblioteca C da equipe: matriz de pixels, paleta, PPM, ASCII |

Boas práticas adotadas: separação de fases com interfaces simples; erros como dados (`Diagnostico`) em vez de `print` espalhado;
AST preservada pelas fases seguintes (dataclasses mutáveis); núcleo testável sem CLI; biblioteca C compilada com `-Wall -Wextra` (e `-Werror` nos testes);
nenhuma dependência externa; testes automatizados; repositório Git recomendado (ver §10).

## 7. Mapeamento para C

| TinyDraw | C gerado |
|---|---|
| `tela W por H` | `TDCanvas *c = td_criar(W, H);` |
| `cor N = r,g,b` | `int cor_k = td_definir_cor(c, "N", r, g, b, 'S');` |
| `usar N` | `td_usar(c, cor_k);` |
| `ponto em x,y` | `td_ponto(c, x, y);` |
| `linha de … ate …` | `td_linha(c, x1, y1, x2, y2);` |
| `retangulo em … tamanho …` | `td_retangulo(c, x, y, w, h);` |
| `salvar "f"` | `td_salvar(c, "f");` seguido de `td_imprimir_ascii(c);` |

Cada comando gera também um `printf("[linha N] …")`, tornando observável a correspondência entre o programa-fonte e a execução.
A biblioteca guarda os pixels como **índices de paleta** (`unsigned char`), grava PPM binário (P6) e imprime o ASCII
(`.` = fundo, cada cor com a inicial do nome, resolvendo colisões).
Os dados e comandos vêm exclusivamente do programa na DSL; a biblioteca apenas executa.

## 8. Exemplo completo

**Entrada (`exemplos/validos/sobreposicao.td`):**
```
tela 24 por 12
cor VERMELHO = 255, 0, 0
cor AZUL     = 0, 0, 255
usar VERMELHO
retangulo em 2, 2 tamanho 10 por 7
usar AZUL
retangulo em 7, 4 tamanho 10 por 7
linha de 0, 0 ate 23, 0
linha de 0, 11 ate 23, 11
salvar "sobreposicao.ppm"
```
**Saída ASCII do executável:**
```
+------------------------+
|AAAAAAAAAAAAAAAAAAAAAAAA|
|........................|
|..VVVVVVVVVV............|
|..V........V............|
|..V....AAAAAAAAAA.......|
|..V....A...V....A.......|
|..V....A...V....A.......|
|..V....A...V....A.......|
|..VVVVVAVVVV....A.......|
|.......A........A.......|
|.......AAAAAAAAAA.......|
|AAAAAAAAAAAAAAAAAAAAAAAA|
+------------------------+
```
Note o cruzamento: onde o azul passa por cima do vermelho, o pixel é azul (regra de sobreposição).

**Diagnósticos (`exemplos/invalidos/erro_semantico.td`, trecho):**
```
erro_semantico.td:2:1: erro semântico: 'ponto' usado antes de declarar a 'tela'
erro_semantico.td:6:1: erro semântico: componente B da cor 'AZUL' vale 300; deve estar entre 0 e 255
erro_semantico.td:11:1: erro semântico: ponto (20, 5) fora da tela 20x10 (x deve estar em 0..19 e y em 0..9)
erro_semantico.td:12:1: erro semântico: linha deve ser horizontal (mesmo y) ou vertical (mesmo x); diagonais não são suportadas
```

## 9. Testes

`py -m unittest discover -v` — consulte os resultados desta revisão em [RELATORIO_REVISAO.md](RELATORIO_REVISAO.md).

| Arquivo | Cobertura |
|---|---|
| `test_lexer.py` | tokens, palavras reservadas, sinônimos acentuados, comentários, posição, caractere inválido, `-5`, string aberta |
| `test_parser.py` | todos os comandos, falta de `por`, comando inválido, fim inesperado, vírgula ausente, palavra reservada como nome |
| `test_semantica.py` | regras S1–S15 (um teste por regra, mais programa válido) |
| `test_geracao.py` | estrutura do C; **ponta a ponta**: compila com `-Werror`, executa e confere os pixels do PPM (incluindo sobreposição); todos os exemplos válidos compilam; todos os inválidos são rejeitados sem gerar código |

Programas de exemplo: válidos `casa.td`, `sobreposicao.td`, `moldura.td`; inválidos `erro_lexico.td` (3 erros léxicos),
`erro_sintatico.td`, `erro_semantico.td` (12 erros + 2 avisos).

## 10. Limitações e evolução

**Limitações:** só contorno de retângulo; sem diagonais; sem repetição, variáveis ou expressões; apenas o primeiro erro sintático é
reportado (sem recuperação de erros); saída nativa do C em PPM; conversão PNG disponível no Python.
**Evolução possível:** `preencher` (retângulo cheio); linhas diagonais (Bresenham); círculos; `repetir N { … }`; transformações de posição;
camadas; recuperação de erros no parser (modo pânico).

## 11. Uso de IA e autoria

Consulte [AUTORIA_E_IA.md](AUTORIA_E_IA.md). As atribuições anteriores a
ferramentas e as verificações supostamente feitas pela equipe não foram
comprovadas nesta revisão. Registre somente fatos e evidências reais.

## 12. Memorial de participação *(preencher)*

| Integrante | Responsabilidades | Evidências (commits, arquivos, reuniões) |
|---|---|---|
| Antonio Marcos dos Santos Junior | | |
| Fernando Augusto da Silva | | |
| Raphael Antonio dos Santos Rangel | | |

Sugestão de divisão: (1) léxico + parser; (2) semântica + tabela de símbolos; (3) gerador de C + biblioteca + testes/documentação.
Todos devem saber explicar **todas** as partes: a nota depende da verificação de autoria na apresentação oral.

---

## 13. Extensão opcional: TinyDraw Studio (interface + assistente local por regras)

### 13.1 Motivação e limites
O Studio facilita a demonstração: o usuário descreve o desenho em português e vê o programa `.td`, o C gerado,
o log de execução e a imagem. **Não altera a proposta**: a linguagem, as regras léxicas/sintáticas/semânticas, o
transpilador e o C gerado são exatamente os do núcleo (§2–§8). O fluxo exigido continua sendo
`programa na DSL -> transpilador em Python -> programa C -> executável -> resultado visível`.

### 13.2 Princípio de projeto
**O assistente nunca desenha.** Ele apenas escreve texto na linguagem TinyDraw. Esse texto é tratado como qualquer
programa-fonte escrito à mão: passa por léxico, sintaxe e semântica; só então vira C, é compilado e executado.
Assim, "os dados, comandos e comportamentos apresentados" vêm do programa-fonte na DSL, como pede o catálogo.

```
pedido (pt) --> assistente --> programa .td --> lexer --> parser --> semântica --> codegen --> .c --> gcc --> exe --> .ppm
                 `-- local (regras, sem internet)
```

### 13.3 Assistente local (modo offline)
Interpretador por regras (expressões regulares sobre texto normalizado, sem acentos): reconhece figuras
(retângulo, quadrado, moldura, linha, ponto, círculo, triângulo, sol, casa, árvore), cores, medidas
(`10 por 5`, `lado`, `raio`, `base`...), preenchimento e posições (`em 3, 4`, `no centro`, cantos...). Convenção:
(x, y) é o canto superior esquerdo da caixa que envolve a figura. Etapas: (1) localizar a tela; (2) fatiar o pedido
em figuras a cada palavra de figura; (3) extrair atributos de cada fatia; (4) **layout** (tela automática,
distribuição horizontal das figuras sem posição, ajuste para caber); (5) emissão do `.td`. Figuras
sem comando próprio são compostas de comandos existentes (disco = linhas horizontais; triângulo = linhas empilhadas).
Valores fora da tela são ajustados e registrados no log do assistente.

### 13.4 Arquitetura dos módulos novos
| Módulo | Responsabilidade |
|---|---|
| `assistente.py` | Fachada `gerar(pedido, progresso=...)`; tipos `ResultadoGeracao` e `ErroAssistente` |
| `assistente_local.py` | Interpretador por regras, layout e emissão do `.td` |
| `executor.py` | Localiza o gcc (variável `CC`, pasta `gcc\` ao lado do .exe, PATH), compila e executa |
| `pipeline.py` | `executar_programa` (do `.td` à imagem), `etapas`, diagnóstico e autoteste |
| `imagem.py` | Leitura de PPM e escrita de PNG (sem bibliotecas externas) |
| `caminhos.py` | Localiza `runtime/` e `exemplos/` dentro ou fora do .exe (PyInstaller) |
| `gui.py` | Interface tkinter: editor, abas, barra de etapas, trabalho em segundo plano (thread + fila) |

### 13.5 Testes da extensão
`test_assistente_local.py` (pedidos específicos; **400 pedidos aleatórios** que precisam gerar programa aceito pelo
compilador; ponta a ponta conferindo um pixel),
`test_pipeline.py` (estados das etapas, imagem antiga nunca reaproveitada, PNG, autoteste) e `test_gui_smoke.py`
(abre a janela, gera pelo assistente local e confere a imagem; opcional). Testes de mutação eram mencionados no documento original, mas não foram reproduzidos nesta revisão; não são evidência validada.

### 13.6 Empacotamento
`construir_exe.bat` usa PyInstaller (`--onefile --windowed`) levando `runtime/` e `exemplos/` dentro do executável.
O .exe depende do gcc do computador (ou de `gcc\bin\gcc.exe` ao lado dele). `TinyDrawStudio.exe --autoteste` e
*Ajuda -> Diagnóstico* verificam o ambiente.

### 13.7 Limitações
O assistente local reconhece um vocabulário limitado; o Studio não faz desfazer/refazer do desenho (o editor tem Ctrl+Z para o texto).

## Notas da revisão

A implementação permite declarar e selecionar cores antes de `tela`; desenhar e salvar exigem a tela anterior. Começar pela tela é a convenção dos exemplos, não uma regra sintática. O leitor PPM aceita o P6 específico do runtime, sem comentários no cabeçalho. Veja o guia de estudos e o relatório para os limites das verificações.
