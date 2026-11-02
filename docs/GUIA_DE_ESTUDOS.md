# TinyDraw — guia de estudos e defesa do projeto

Material para Antonio Marcos dos Santos Junior, Fernando Augusto da Silva e
Raphael Antonio dos Santos Rangel. Revisão de 02/11/2026, baseada nos arquivos
entregues e no código desta pasta.

O edital exige compreensão do material, da linguagem e das decisões técnicas.
Verificação insuficiente de autoria ou de apropriação pode dar **nota zero ao
grupo**. IA é permitida como apoio, desde que declaradas as ferramentas,
finalidades e verificações. Este guia não comprova autoria, não atribui tarefas
passadas e não é um texto para decorar. O registro a completar com fatos está
em [AUTORIA_E_IA.md](AUTORIA_E_IA.md).

Estudem com o projeto aberto. Para cada tema: expliquem sem ler, localizem a
implementação, prevejam um resultado, executem e investiguem diferenças. Quem só
consegue repetir a definição ainda precisa praticar com o código.

## Como usar o material

Há doze partes. Na primeira leitura, acompanhem 1–8 e o exemplo da parte 10.
Depois usem a parte 9 para navegar pelas funções. Respondam à parte 11 sem
consultar a resposta e realizem a parte 12 alternando os papéis.

| Parte | O que deve conseguir demonstrar ao terminar |
|---|---|
| 1. Introdução | Justificar a DSL e as linguagens usadas |
| 2. Arquitetura | Rastrear dados desde o arquivo até a imagem |
| 3. Léxico | Reconhecer tokens, posições e erros de caracteres |
| 4. Sintaxe e AST | Derivar comandos da EBNF e construir seus nós |
| 5. Semântica | Simular tabela de cores e estado do analisador |
| 6. C gerado | Relacionar cada figura com chamadas e pixels |
| 7. Compilação e imagem | Distinguir C, executável, PPM e PNG |
| 8. Studio | Explicar UI, threads, assistentes e prévia |
| 9. Código | Informar entradas, saídas e relações dos módulos |
| 10. Execução completa | Prever e conferir uma imagem de 6 × 4 |
| 11. Perguntas | Defender decisões, limites e casos difíceis |
| 12. Demonstração | Apresentar o fluxo e falhas de forma reproduzível |

## Parte 1 — Introdução

### O problema que foi delimitado

Uma imagem pode ser vista como uma grade de pixels. Para desenhar um retângulo
em C, alguém precisa criar essa grade, selecionar uma cor, descobrir as bordas,
escrever nos índices corretos e gravar os bytes de um formato de imagem. Esses
detalhes são úteis na implementação, mas tornam trabalhosa a descrição de uma
cena simples.

TinyDraw separa a **descrição do desenho** do **mecanismo que o realiza**.
`retangulo em 1, 1 tamanho 4 por 3` descreve uma figura; a biblioteca C calcula
as bordas. O transpilador confere antes se essa figura cabe na tela.

O usuário visado é quem quer experimentar desenhos simples e estudar compiladores.
O domínio é deliberadamente pequeno: tela, cores e figuras ortogonais. Não há
pretensão de substituir Python, C ou um editor gráfico completo.

### DSL e linguagem de propósito geral

DSL significa linguagem de domínio específico. Seu vocabulário é escolhido para
um conjunto restrito de tarefas. SQL, por exemplo, tem vocabulário voltado a
consultas; TinyDraw tem vocabulário voltado a desenhos. C e Python permitem
resolver muitos tipos de problema, enquanto a gramática TinyDraw não oferece
operações genéricas de rede, arquivos arbitrários ou cálculo de expressões.

TinyDraw é uma DSL porque suas construções representam diretamente o domínio:
`tela`, `cor`, `usar`, `ponto`, `linha`, `retangulo` e `salvar`. Não basta ter
palavras em português para ser DSL; é a delimitação das operações que a caracteriza.

### Por que Python, C e GCC

Python facilita manipular texto, regex, listas, dicionários e dataclasses, além
de permitir testar cada fase isoladamente. Neste projeto o lexer usa `re`, o
parser é manual e a AST é uma coleção de objetos Python. Isso reduz o trabalho
de infraestrutura necessário para estudar o processo de tradução.

C foi escolhido como linguagem-alvo do transpilador, conforme o DAC. Neste fluxo,
é uma representação entre a DSL e o executável nativo. O C gerado é legível e
auditável: a equipe consegue apontar a chamada que corresponde a cada comando.
Não é uma representação intermediária de baixo nível como bytecode ou LLVM IR.

GCC compila o C gerado e a biblioteca C auxiliar, e faz a ligação das chamadas
com suas implementações para produzir o executável. Ele não lê `.td` nem valida
coordenadas TinyDraw. Um programa pode ser C válido e representar um desenho
incorreto; por isso a comparação de pixels também é necessária.

**Explique sem consultar:** por que não basta mostrar uma imagem produzida por um
assistente? Porque o produto acadêmico inclui formalizar e implementar a tradução
da DSL; a imagem precisa vir do C correspondente àquela fonte.

## Parte 2 — Arquitetura

### As duas entradas do sistema

Na CLI, `tinydraw/__main__.py` chama `cli.principal()`, que lê o arquivo `.td`.
No Studio, `tinydraw_studio.py` chama `gui.iniciar()`, cria `App` e recebe texto
do editor. Ambos convergem para `compilador.transpilar(texto, origem)`.

```text
CLI: arquivo → read_text ──────────────┐
                                     ├→ transpilar → tokens → AST → tabela → C
Studio: editor → pipeline ────────────┘                                  │
                                                                         ↓
                                               executor.compilar → executável
                                                                         │
                                                   executor.executar → PPM
                                                                         │
                                               imagem.ler_ppm → RGB → PNG
```

O núcleo `transpilar` não grava arquivos nem abre processos. Ele retorna um
`Resultado` com tokens, AST, tabela, diagnósticos e, quando válido, código C.
A separação permite testar uma falha léxica sem depender de GCC ou de janela.

O `pipeline.executar_programa` acrescenta as operações de arquivo, compilação,
execução e preparação da prévia. A CLI realiza sua própria gravação de C e usa
o mesmo `executor`. A conversão PNG é feita no Python depois da execução C.

### Estrutura e responsabilidades

| Diretório/arquivo | Responsabilidade |
|---|---|
| `tinydraw/lexer.py` | Caracteres → tokens posicionados |
| `tinydraw/parser.py` | Tokens → comandos estruturados |
| `tinydraw/ast_nodes.py` | Classes dos nós e representação textual da AST |
| `tinydraw/semantica.py` | Regras de contexto, tabela e estado do programa |
| `tinydraw/codegen.py` | AST validada + tabela → texto C |
| `tinydraw/compilador.py` | Coordena as quatro fases anteriores |
| `tinydraw/erros.py` | Estrutura comum de erro/aviso e exceção do parser |
| `tinydraw/executor.py` | Descobre compilador, compila e executa |
| `tinydraw/cli.py` | Argumentos, leitura da fonte, gravação e retorno no terminal |
| `tinydraw/pipeline.py` | Resultado completo e estados mostrados no Studio |
| `tinydraw/gui.py` | Widgets, eventos, abas e coordenação de trabalho |
| `tinydraw/assistente.py` | Seleção do gerador de texto e resultado comum |
| `tinydraw/assistente_local.py` | Regras locais que escrevem `.td` |
| `tinydraw/imagem.py` | Leitura do P6 do runtime e codificação PNG |
| `tinydraw/caminhos.py` | Recursos no fonte e no pacote PyInstaller |
| `runtime/tinydraw.h` | Tipos e protótipos públicos da biblioteca C |
| `runtime/tinydraw.c` | Paleta, grade de pixels, figuras, PPM e ASCII |
| `tests/` | Casos automatizados válidos, inválidos e de integração |
| `exemplos/` | Fontes `.td` para uso e apresentação |
| `ferramentas/` | Conversão e rastreamento do exemplo de estudo |

### Compilador, transpilador e interpretador

Compilar é traduzir um programa para outra representação. Um transpilador é
um compilador que traduz entre linguagens de nível semelhante: aqui, TinyDraw
para C. GCC faz a etapa seguinte até o código de máquina.

Um interpretador executa as operações da linguagem a partir de sua representação,
sem precisar produzir o programa C deste fluxo. TinyDraw não interpreta os
comandos de desenho em Python para gerar o PPM. `assistente_local.interpretar` tem esse
nome porque interpreta um pedido em português; seu retorno é fonte `.td`, não
uma imagem. O nome da função não muda a arquitetura do compilador.

**Exercício:** localize quem grava `.c` na CLI e no Studio. São `cli.principal`
e `pipeline.executar_programa`; `Gerador.gerar` apenas monta a string.

## Parte 3 — Análise léxica

### Token, lexema, valor e posição

Token é uma unidade classificada para o parser. Em `tela 6 por 4`, o lexer
retorna tipos `TELA INT POR INT`. O lexema de `INT` é o texto `"6"`; seu valor
é o inteiro Python `6`. Linha e coluna começam em 1 e permitem apontar o erro.

Trecho real de `lexer.py`:

```python
@dataclass(frozen=True)
class Token:
    tipo: str
    lexema: str
    valor: Any
    linha: int
    coluna: int
```

`frozen=True` impede atribuir novos valores aos campos do token. Isso não vale
para a AST: seus nós usam dataclasses comuns, mutáveis.

### Expressões regulares reais

O módulo monta uma expressão com grupos nomeados a partir de `ESPECIFICACAO`.
`_REGEX.finditer(texto)` percorre os casamentos. A ordem das alternativas importa.

| Categoria | Regex | Tratamento |
|---|---|---|
| Comentário | `\#[^\n]*` | Ignora até antes da quebra de linha |
| Espaço | `[ \t\r]+` | Ignora espaços, tabs e retorno de carro |
| Nova linha | `\n` | Incrementa linha e redefine início da linha |
| String | `"[^"\n]*"` | Remove aspas externas do valor |
| String aberta | `"[^\n]*` | Diagnóstico de aspas não fechadas |
| Inteiro | `[0-9]+` | Converte o lexema com `int` |
| Identificador | `[^\W\d]\w*` | Reclassifica reservadas ou mantém ID |
| Vírgula | `,` | Token `VIRGULA` |
| Igual | `=` | Token `IGUAL` |
| Desconhecido | `.` | Diagnóstico de caractere inesperado |

`\w` segue o comportamento Unicode do Python; o padrão de ID admite `_` e
caracteres Unicode de palavra que não sejam dígitos no início. Os exemplos usam
nomes simples. Isso não significa que identificadores sejam limitados a ASCII.

A alternativa de string válida vem antes da string aberta. A alternativa de
identificador reconhece a palavra inteira: `telado` é um ID, não `TELA` seguido
de `do`. A classificação de reservadas acontece depois de reconhecer o ID.

### Reservadas e sinônimos

`PALAVRAS_RESERVADAS` contém `tela`, `cor`, `usar`, `ponto`, `linha`, `retangulo`,
`salvar`, `em`, `de`, `ate`, `tamanho`, `por`. `SINONIMOS` transforma `até` em
`ate` e `retângulo` em `retangulo`. O lexema original continua preservado.
`TELA` é ID: não há conversão geral para minúsculas no lexer da DSL.

```python
normal = SINONIMOS.get(lex, lex)
if normal in PALAVRAS_RESERVADAS:
    tokens.append(Token(normal.upper(), lex, normal, linha, coluna))
else:
    tokens.append(Token("ID", lex, lex, linha, coluna))
```

O assistente local normaliza frases para minúsculas e remove acentos em outro
módulo. Não confunda essa normalização do pedido com as regras do `.td`.

### Posições e erros

A coluna é `m.start() - inicio_linha + 1`. O scanner ignora a quebra de linha
como token, mas atualiza a posição. Ao terminar acrescenta `EOF`, mesmo que haja
erros, para marcar o fim da sequência.

`@` é erro léxico. Em `ponto em -1, 0`, `-` é erro léxico, pois não existe
sinal negativo na especificação. Já `tela 0 por 4` é lexicamente válido: zero
é um inteiro reconhecido. A rejeição de dimensão zero é semântica.

Na revisão, uma sequência decimal maior que o limite de conversão ativo do
Python passou a gerar diagnóstico, em vez de escapar como `ValueError`.
Isso é proteção contra uma entrada extrema, não uma nova operação da DSL.

O lexer coleta erros de caracteres/string e `compilador.transpilar` não chama
o parser se houver erro léxico. Por isso uma fonte com `@` pode ter tokens
parciais, mas não tem AST no resultado do orquestrador.

**Prática:** troque `tela` por `TELA`. Não aparece erro léxico: aparece ID,
e depois erro sintático porque o parser esperava um início de comando.

## Parte 4 — Análise sintática e AST

### Gramática e EBNF

Uma gramática define sequências permitidas de categorias. BNF descreve regras
de produção com não terminais e alternativas. EBNF adiciona abreviações como
repetição `{ ... }`. Essas chaves são metassintaxe da documentação; o usuário
não escreve chaves em TinyDraw.

Gramática compatível com `parser.py`:

```ebnf
programa  = { comando } EOF ;
comando   = tela | cor | usar | ponto | linha | retangulo | salvar ;
tela      = "tela" INT "por" INT ;
cor       = "cor" ID "=" INT "," INT "," INT ;
usar      = "usar" ID ;
ponto     = "ponto" "em" INT "," INT ;
linha     = "linha" "de" INT "," INT "ate" INT "," INT ;
retangulo = "retangulo" "em" INT "," INT "tamanho" INT "por" INT ;
salvar    = "salvar" STRING ;
```

`INT`, `ID` e `STRING` são categorias produzidas pelo lexer. `EOF` é um token
interno, não a palavra a digitar no arquivo. Os sinônimos acentuados já chegam
com os tipos normalizados. Um programa vazio satisfaz a repetição sintática,
mas a semântica exige tela e salvar.

### Parser descendente recursivo

`Parser` mantém `tokens` e índice `i`. `_atual()` consulta sem consumir.
`_consumir(tipo, descricao)` verifica o tipo e avança; em desacordo lança
`ErroDeCompilacao` com um `Diagnostico` sintático na posição atual.

`analisar()` cria `ast.Programa` e acrescenta comandos até `EOF`. `_comando()`
escolhe uma função usando o token inicial: `TELA` chama `_tela`, `PONTO` chama
`_ponto`, e assim por diante. Cada comando tem início distinto, portanto basta
um token de antecipação para decidir a produção. Não há backtracking.

Não há expressões aritméticas nem precedência de operadores. A recursão é rasa:
o programa contém uma lista linear de comandos. O nome “descendente recursivo”
refere-se ao estilo de implementar produções por funções, não à existência de
laços ou blocos recursivos na linguagem do usuário.

Trecho real que reconhece um ponto:

```python
def _ponto(self, t):
    self._consumir("EM", "'em'")
    x, y = self._par()
    return ast.Ponto(t.linha, t.coluna, x, y)
```

O token `PONTO` já foi consumido em `_comando`. `_par` exige `INT VIRGULA INT`.
O nó recebe a localização do início do comando para futuros diagnósticos.

### O que fica na AST

AST significa árvore sintática abstrata. Ela retém o significado estrutural,
sem guardar vírgulas e palavras de ligação como nós separados. `ponto em 1, 1`
vira `Ponto(linha=9, coluna=1, x=1, y=1)` no exemplo de estudo.

Uma árvore de derivação completa preservaria mais detalhes da gramática;
a AST remove essa pontuação redundante. Aqui a raiz `Programa` contém uma
lista de comandos, cada qual com campos simples. Não há subexpressões.

`Tela`, `DefCor`, `Usar`, `Ponto`, `Linha`, `Retangulo` e `Salvar` herdam
linha/coluna de `Comando`. `ast_nodes.descrever` monta uma exibição textual,
omitindo localização dos campos e mostrando-a ao final com `@ linha:coluna`.

### Erros sintáticos e fronteira com a semântica

`tela 6 4` reconhece três tokens válidos, mas falta `POR`; falha no parser.
`ponto em 1 1` falha pela vírgula ausente. `cor tela = 1, 2, 3` falha porque
`tela` foi classificado como reservada e o parser exige ID como nome.

`linha de 0, 0 ate 3, 3` tem a estrutura certa. Só a semântica rejeita a
diagonal. `usar AUSENTE` também tem estrutura certa; é necessário conhecer a
tabela de cores para decidir que o nome não existe.

O parser para no primeiro erro e não recupera a análise. O orquestrador captura
a exceção e devolve o resultado com diagnóstico, sem tabela semântica ou C.

**Prática:** leia `_retangulo` e diga a sequência de tipos que consome. Depois
remova `tamanho` no exemplo e preveja qual token aparecerá como encontrado.

## Parte 5 — Análise semântica

### Estado e tabela de símbolos

A sintaxe responde se a frase tem a forma da linguagem. A semântica responde
se seus comandos fazem sentido no contexto deste programa. O `Analisador`
percorre os comandos da AST na ordem e mantém:

- `tabela`: nomes de cores para objetos `Simbolo`;
- `tela_declarada`: se uma declaração foi encontrada;
- `dim`: `(largura, altura)` somente quando as dimensões são válidas;
- `cor_ativa`: símbolo escolhido pelo último `usar` válido;
- `salvo`: se já apareceu `salvar`;
- `diags`: erros e avisos acumulados.

`Simbolo` contém `nome`, `r`, `g`, `b`, `linha`, `indice` e `usada`.
`TabelaDeSimbolos.declarar` devolve um símbolo novo ou `None` se o nome já
existe. `buscar` devolve o símbolo ou `None`. `todas` devolve uma lista na
ordem de inserção. O dicionário permite consulta média O(1) por nome.

O índice semântico começa em 1 porque a paleta C reserva 0 ao fundo. O gerador
não precisa escrever esse índice como uma constante: usa o retorno de
`td_definir_cor` em uma variável como `cor_1`.

### Regras efetivas

| Comando/contexto | Verificação real |
|---|---|
| Programa | Uma tela e um salvar obrigatórios |
| Tela | Uma única declaração, dimensões 1..1000 |
| Cor | Nome único, cada componente 0..255, até 255 cores declaradas |
| Usar | Nome já declarado; marca `usada=True` e muda cor ativa |
| Desenho | Tela válida e cor ativa anteriores |
| Ponto | `0 <= x < largura`, `0 <= y < altura` |
| Linha | Ambos os extremos dentro e mesmo x ou mesmo y |
| Retângulo | Largura/altura positivas, canto e extensão dentro da tela |
| Salvar | Nome simples, extensão `.ppm`, sem caminhos e compatível com Windows |
| Depois de salvar | Qualquer comando é erro |
| Cor nunca selecionada | Aviso, não erro |
| Linha com extremos iguais | Aviso; equivale a um ponto |

Declarar duas cores é parte da demonstração mínima do projeto, não uma
restrição para cada arquivo. `tela 1 por 1 salvar "x.ppm"` é aceito e gera
uma imagem branca. Do mesmo modo, a implementação permite declarar cores e
selecioná-las antes de `tela`; a tela precisa vir antes de desenhar/salvar.
Começar pela tela é uma convenção didática, não uma exigência geral do parser.

### Coordenadas e contagem de pixels

Uma tela 6 × 4 tem x em 0..5 e y em 0..3. O ponto (6, 0) não cabe.
Um retângulo em (1, 1) com largura 4 e altura 3 termina em (4, 3):
`1 + 4 - 1 = 4` e `1 + 3 - 1 = 3`. O `-1` aparece porque a posição inicial
já conta como primeiro pixel. Usar x+largura como último pixel desenharia
uma coluna a mais.

Trecho real de `_retangulo`:

```python
fx, fy = c.x + c.largura - 1, c.y + c.altura - 1
if fx >= w or fy >= h:
    self._erro(c, f"retângulo ultrapassa a tela {w}x{h} "
                  f"(canto oposto seria ({fx}, {fy}))")
```

Os inteiros Python têm precisão arbitrária, mas o domínio limita os valores
que chegam ao C. Um valor enorme de coordenada em um comando válido de desenho
é barrado antes da emissão. Para esse domínio não há expressões calculadas
em tempo de execução: todas as coordenadas já estão disponíveis na análise.

### Erros, avisos e cascatas

`_erro` e `_aviso` guardam dados, sem imprimir. No fim, os diagnósticos são
ordenados por linha/coluna. `_exige_tela` e `_exige_cor` impedem verificações
que dependam de um estado ausente, reduzindo mensagens em cascata.
Por exemplo, sem dimensão válida não se tenta desempacotar `dim` em `_dentro`.

Uma cor com RGB inválido ainda pode entrar na tabela durante a coleta de erros;
isso não significa que será executada. Basta um erro em `Resultado.erros`
para que `compilador.transpilar` não invoque `Gerador`.

O aviso “nunca usada” quer dizer nunca **selecionada com usar**. Selecionar uma
cor sem desenhar já marca `usada=True`. Não afirme que o analisador prova que
todo símbolo declarado contribuiu com pixels visíveis no resultado final.

### Três exemplos para explicar oralmente

1. `usar VERDE` sem declaração: sintaxe aceita, `buscar` retorna `None`, erro
   semântico; C não é gerado.
2. `linha de 0, 0 ate 2, 2`: tokens e AST válidos, `_linha` detecta mudanças
   simultâneas em x e y, erro semântico de diagonal.
3. `retangulo em 4, 2 tamanho 3 por 2` numa tela 6 × 4: canto inicial válido,
   mas canto oposto x=6 inválido; erro semântico de extensão.

**Exercício:** troque `usar AZUL` por `usar VERMELHO` no exemplo. Ele continua
válido, mas a aparência muda e AZUL recebe aviso de nunca selecionada. Um
compilador não pode adivinhar que a intenção do usuário era desenhar em azul.

## Parte 6 — Geração de código C

### Como a AST vira texto

`Gerador(programa, tabela)` recebe uma AST já validada e a tabela. `gerar(origem)`
monta uma lista de linhas em `self.saida`, depois une com `"\n"`. Não executa
nenhum comando do desenho. O código resultante inclui `stdio.h` e `tinydraw.h`
e define `int main(void)`.

| Nó | Emissão principal |
|---|---|
| `Tela` | `TDCanvas *c = td_criar(W, H);` |
| `DefCor` | `int cor_N = td_definir_cor(c, "NOME", r, g, b, simbolo);` |
| `Usar` | `td_usar(c, cor_N);` |
| `Ponto` | `td_ponto(c, x, y);` |
| `Linha` | `td_linha(c, x1, y1, x2, y2);` |
| `Retangulo` | `td_retangulo(c, x, y, largura, altura);` |
| `Salvar` | Chamada verificada a `td_salvar` |

Há comentários e `printf` com a linha original. Eles ajudam a rastrear a
tradução, mas os pixels são produzidos pelas funções `td_*`, não pelo log.
No final são chamados `td_imprimir_ascii` e `td_liberar`.

O gerador usa nomes C como `cor_1`, em vez de copiar identificadores Unicode
para variáveis C. O nome TinyDraw continua como string para a legenda. A tabela
local `cores` associa o nome TinyDraw à variável C já declarada.

`_escapar_c` trata barra invertida, aspas, nova linha e `?` em strings.
O nome do arquivo passa como argumento de `%s`, sem se tornar a string de
formato do `printf`. Por isso um `%` no nome não vira uma diretiva de formatação.
O comentário de origem também remove fechamento de comentário e quebras de linha.

### Biblioteca auxiliar e representação de pixels

Trecho real do cabeçalho, com campos centrais:

```c
typedef struct {
    int largura, altura;
    unsigned char *pixels;
    TDCor paleta[TD_MAX_CORES];
    int ncores;
    int cor_ativa;
} TDCanvas;
```

`TD_MAX_CORES` é 256. Cada pixel guarda **um índice de paleta**, não três bytes
RGB. A paleta armazena RGB, nome e símbolo ASCII de cada cor. O fundo ocupa
índice 0 com (255,255,255). Até 255 entradas adicionais cabem em `unsigned char`.

`td_criar` usa `calloc` para o canvas e para `largura*altura` posições. Como
`calloc` zera a memória, todos os pixels começam apontando para a cor 0.
O cast para `size_t` ocorre antes da multiplicação do tamanho. A semântica
limita o domínio normal de uso a 1000 × 1000.

O índice linear de (x,y) é `y * largura + x`. Para largura 6, (1,1) ocupa
posição 7, (5,0) ocupa 5 e (5,3) ocupa 23. É uma matriz lógica armazenada
como vetor contínuo por linhas, não uma lista de ponteiros para linhas.

### Algoritmos de desenho

`td_ponto` verifica limites e escreve o índice da cor ativa:

```c
c->pixels[(size_t)y * c->largura + x] = (unsigned char)c->cor_ativa;
```

Essa atribuição explica a sobreposição: não soma nem mistura cores. A última
escrita substitui o índice anterior. Não há transparência ou canal alfa.

`td_linha` testa primeiro se y1==y2 e percorre x; caso contrário, testa x1==x2
e percorre y. Usa menor/maior extremo e laço inclusivo `i <= b`. Assim a linha
funciona mesmo com extremos invertidos. Caso ambos os extremos sejam iguais,
o ramo horizontal desenha uma única posição. Diagonais não têm algoritmo no
runtime; o uso normal já as rejeita na semântica.

`td_retangulo` calcula x2=x+w−1 e y2=y+h−1 e chama quatro linhas: superior,
inferior, esquerda e direita. Os cantos podem ser escritos mais de uma vez,
mas sempre na mesma cor, sem efeito visual adicional. Largura ou altura 1
fazem lados coincidirem; o resultado continua sendo o contorno degenerado.
O interior nunca é preenchido por essa função.

### Memória, confiança entre fases e limites

`main` testa se `td_criar` retornou NULL e encerra com erro se faltou memória.
Depois de salvar, libera o vetor de pixels e o canvas. A biblioteca verifica
alguns limites defensivamente, mas é usada com dados previamente validados.
Não é uma interface C genérica completamente protegida contra qualquer chamada manual.

Adicionar verificações no runtime não substitui a semântica: a mensagem deve
apontar o comando `.td` antes de o usuário esperar pela compilação.

### Custo dos algoritmos

Um ponto custa O(1). Uma linha custa O(comprimento). Um contorno custa O(w+h),
considerando quatro lados. Salvar e imprimir a grade custam O(W×H). Os pixels
ocupam W×H bytes, além do canvas/paleta; o PPM contém 3×W×H bytes de raster.
PNG ainda cria buffers de linhas e compressão no Python, portanto usa memória
adicional. A ampliação por fator f faz o raster visual ter f² vezes mais pixels.

**Prática:** explique por que duas cores com o mesmo símbolo ASCII ainda podem
aparecer corretamente no PPM. O símbolo serve à legenda textual; RGB e índices
da paleta permanecem separados.

## Parte 7 — Compilação, execução e imagem

### Descoberta do compilador e comando

`executor.achar_compilador_c` procura, nesta ordem, `CC`, uma pasta portátil
`gcc/bin/gcc.exe` ao lado do executável/aplicação no Windows, e `gcc`, `cc`,
`clang` pelo PATH. `CC` é um caminho ou nome de programa, não uma linha contendo
argumentos. `_ambiente` antepõe a pasta do compilador ao PATH do processo filho.

O comando construído por `compilar` equivale a:

```powershell
gcc -std=c99 -Wall -Wextra -o build/estudo/estudo.exe build/estudo/estudo.c runtime/tinydraw.c -Iruntime
```

Na implementação os caminhos são absolutos quando vêm do pipeline e o comando
é uma lista de argumentos passada a `subprocess.run`, sem `shell=True`.
Assim caminhos com espaços são um argumento único. `-I` informa onde procurar
o cabeçalho; o arquivo `.c` do runtime fornece as implementações para ligação.
Nos testes de geração, `-Werror` torna avisos falhas.

O processo de compilação tem limite de 60 segundos nesta revisão e devolve
`(ok, log, caminho_do_exe_ou_None)`. Sem compilador, há uma mensagem explicativa.
Falhas ao iniciar o processo ou timeout viram resultado de falha, sem encerrar
o Studio com exceção.

### Execução e diretório de trabalho

`executor.executar(exe, cwd, limite_s=20)` roda o binário com `cwd` na pasta
de saída, captura stdout/stderr e retorna código de saída + texto.
O C abre `"estudo.ppm"` relativamente a esse diretório. Retorno 0 indica que o
processo informou sucesso; o pipeline também verifica a existência da imagem.
Timeout retorna 124; falha ao iniciar retorna 126. Nenhum desses casos deve ser
confundido com um erro da gramática.

O pipeline remove o PPM anterior de mesmo nome antes de uma nova tentativa de
compilação válida, para não apresentar uma imagem antiga como resultado novo.
Uma fonte inválida retorna antes disso: arquivos antigos podem continuar em
disco, embora o resultado atual não tenha imagem. A CLI também não limpa todas
as saídas anteriores. Demonstre rejeição em uma pasta nova.

### O formato PPM

PPM representa pixels RGB sem compressão. O runtime grava a variante binária P6:

```text
P6\n
6 4\n
255\n
[72 bytes de pixels RGB, sem separadores textuais]
```

As três primeiras linhas de fato contêm quebras de linha, não os dois caracteres
barra+n. “P6” identifica a variante; “6 4” são dimensões; “255” é o máximo de
cada canal. Depois vêm trios R,G,B, linha por linha, de cima para baixo.
Uma imagem 6 × 4 tem 24 pixels e 72 bytes de raster, mais 11 de cabeçalho,
totalizando 83 bytes para esse cabeçalho específico.

`td_salvar` percorre o vetor de índices, busca cada cor na paleta e grava três
bytes por pixel com `fwrite`. A revisão verifica falha de escrita e fechamento,
pois abrir o arquivo não garante que todos os dados chegaram ao disco.
Falha de gravação retorna erro para o `main` gerado.

### Conversão para PNG e prévia

`ler_ppm(dados)` retorna largura, altura e bytes RGB. É um leitor do formato
específico emitido aqui: três linhas simples de cabeçalho, P6 e máximo 255.
Não implementa todos os cabeçalhos/comentários que um leitor PPM geral aceitaria.
Dimensões não positivas e tamanho inconsistente do raster são rejeitados.

`rgb_para_png(w,h,rgb,fator)` amplia por vizinho mais próximo: cada pixel é
repetido horizontalmente e cada linha verticalmente. O RGB original não muda.
Cada linha recebe byte de filtro 0; `zlib` comprime o conteúdo para o bloco IDAT.
O arquivo inclui assinatura PNG, IHDR com dimensões/tipo, IDAT e IEND. Cada
bloco contém comprimento, tipo, dados e CRC. Não é preciso instalar Pillow.

`fator_para_caber` calcula um fator inteiro pelo espaço disponível, mínimo 1.
Não reduz imagens grandes; o Studio oferece rolagem. A exportação PNG usa a
prévia ampliada, enquanto a exportação PPM copia o arquivo original.

**Verificação importante:** o C, o PPM e o PNG são artefatos diferentes.
`--so-c` funcionar não prova que o GCC compilou; PNG sintético converter não
prova que o C produziu pixels corretos.

## Parte 8 — TinyDraw Studio

### Interface e interação

`gui.App` herda de `tk.Tk`. A montagem cria menus, campos do assistente, editor,
barra de etapas, abas e rodapé. O editor é `tk.Text`; a imagem usa `tk.Canvas`
e `tk.PhotoImage`. A referência à imagem fica em `self._foto`, evitando que a
coleta de lixo remova o objeto enquanto ele é mostrado.

`acao_executar` captura o texto do editor e a área de visualização, depois
chama `pipeline.executar_programa` em segundo plano. `_mostrar_resultado` recebe
o retorno, atualiza abas, marca linhas com tags `erro`/`aviso` e monta a prévia.
Uma fonte rejeitada fica com `codigo_c=None` e não produz prévia atual.

### Por que thread e fila

GCC, execução e rede podem demorar. Rodá-los diretamente no callback Tk
congelaria a janela. `_rodar` inicia uma thread daemon e marca `_ocupado` para
evitar dois trabalhos simultâneos. A thread coloca resultados em `self.fila`.
`_poll`, agendado por `after(80, ...)`, consulta a fila na thread da interface
e executa o callback final. O código em segundo plano não deve tocar widgets.

Esse padrão separa trabalho e apresentação. `queue.Queue` sincroniza a troca
de dados; não é uma fila de comandos da linguagem. A interface não participa
da validação sintática ou das regras geométricas.

### Assistente local

`assistente.gerar` encaminha para `gerar_local`.
O modo local é um sistema de regras, sem modelo treinado e sem rede.
`normalizar` usa Unicode NFD, remove marcas de acento, põe minúsculas e ajusta
espaços. `interpretar` encontra tela, divide a frase por palavras de figuras,
extrai cores/medidas/posições e cria objetos `Figura`.

`_layout` define dimensões e posições, ajusta figuras redimensionáveis para
caber e pode descartar figuras fixas que não caibam. `_desenhar` manda operações
ao `Emissor`, que cria texto TinyDraw. `gerar_local` submete esse texto ao
transpilador e devolve `ResultadoGeracao(codigo, valido, log, modo)`.

Um preenchimento vira várias linhas; `Emissor.cheio` escolhe percorrer a menor
quantidade de linhas/colunas entre as duas dimensões. `disco` calcula larguras
com uma raiz quadrada e emite segmentos horizontais. `triangulo` aumenta a
meia largura a cada linha. Casa e árvore são composições de formas.
Essas operações escrevem `.td`; o Python não grava o desenho final no lugar do C.

O limite do assistente local é `MAX_TELA=200`, diferente do limite 1000 da DSL.
O primeiro é uma política do gerador de pedidos; o segundo é uma regra do
analisador semântico. Uma frase pode gerar um programa válido que não corresponde
perfeitamente à intenção do usuário; aceitação do compilador não prova fidelidade
da interpretação de linguagem natural.

### Recursos e empacotamento

`caminhos.raiz_recursos` usa a raiz do fonte ou `_MEIPASS` quando empacotado.
PyInstaller deve incluir `runtime/` e `exemplos/` como dados. A biblioteca C
incluída continua sendo fonte C: o GCC não está embutido no executável Studio.
O `--autoteste` do ponto de entrada também grava um arquivo para consulta no
pacote sem console.

**Prática:** deixe o assistente de lado, abra um `.td` e execute F5. Explique
por que o compilador continua completo mesmo sem interpretação de pedidos.

## Parte 9 — Estudo das interfaces do código

Esta seção serve para navegar com o editor aberto. Nomes iniciados por `_`
são detalhes internos por convenção; o Python não impõe privacidade.

### Reconhecimento, AST e diagnósticos

| Arquivo / função ou classe | Parâmetros essenciais | Retorno/efeito | Relação e exemplo |
|---|---|---|---|
| `lexer.tokenizar` | `texto: str` | `(List[Token], List[Diagnostico])` | `tela 6 por 4` gera TELA, INT, POR, INT, EOF; consumido pelo parser |
| `lexer.Token` | tipo, lexema, valor, linha, coluna | Registro imutável | INT guarda valor 6 sem perder lexema `6` |
| `parser.Parser` | lista de tokens terminada em EOF | Instância com índice de leitura | Criada em `transpilar` após léxico sem erro |
| `Parser.analisar` | Usa a lista da instância | `ast.Programa` ou exceção | Percorre `_comando` até EOF |
| `Parser._consumir` | tipo esperado, descrição | Token e avanço ou exceção | Falta de POR em `tela 6 4` |
| `Parser._par` | Usa tokens atuais | Tupla `(x,y)` | Reutilizada em ponto, linha e retângulo |
| `ast_nodes.Programa` | `comandos` opcional | Raiz com lista | Recebe Tela, DefCor, etc. |
| `ast_nodes.Comando` e subclasses | localização e campos específicos | Nó de dados | `Ponto(9,1,1,1)` representa linha 9, posição (1,1) |
| `ast_nodes.descrever` | `prog: Programa` | String de exibição | Usada por `--ast`; não gera C |
| `erros.Diagnostico.formatar` | nome do arquivo | String localizada | `fonte.td:2:1: erro sintático: ...` |
| `erros.ErroDeCompilacao` | lista de diagnósticos | Exceção com atributo diagnosticos | Parser lança; compilador captura |

Trecho real de `ast_nodes.descrever`:

```python
campos = ", ".join(f"{k}={v!r}" for k, v in vars(c).items()
                   if k not in ("linha", "coluna"))
```

`vars(c)` acessa os campos do nó. Essa função só formata o que já está na AST;
não volta à fonte nem repete o parser. `!r` mantém aspas em nomes/strings para
ajudar a leitura.

### Semântica, geração e coordenação

| Arquivo / função ou classe | Parâmetros essenciais | Retorno/efeito | Relação e exemplo |
|---|---|---|---|
| `semantica.Simbolo` | nome, RGB, linha, índice, usada | Registro de cor | Associa AZUL a (0,0,255) |
| `TabelaDeSimbolos.declarar` | nome, r,g,b, linha | Simbolo ou None | Segundo AZUL é duplicata |
| `TabelaDeSimbolos.buscar` | nome | Simbolo ou None | `usar AZUL` resolve o nome |
| `TabelaDeSimbolos.todas` | nenhum | Lista de símbolos | Gerador escolhe legenda ASCII |
| `Analisador.analisar` | `prog` | `(tabela, diagnósticos)` | Visita AST mantendo estado |
| `Analisador._dentro` | comando, x,y, rótulo | bool e eventual erro | (6,0) fora de tela 6 × 4 |
| `codegen.atribuir_simbolos` | tabela | Dicionário nome → caractere | AZUL pode receber A |
| `codegen.Gerador` | programa, tabela validados | Instância que acumula linhas | Não deve receber AST rejeitada |
| `Gerador.gerar` | origem opcional | String C completa | `td_ponto(c, 1, 1);` |
| `compilador.transpilar` | texto, origem opcional | `Resultado` | Chamada comum de CLI, pipeline e assistentes |
| `compilador.Resultado` | tokens, ast, tabela, diagnósticos, C | Contêiner com propriedades | `erros`, `avisos`, `sucesso` derivam dos diagnósticos |

Trecho real do orquestrador:

```python
res.tabela, sem = Analisador().analisar(res.ast)
res.diagnosticos += sem
if res.sucesso:
    res.codigo_c = Gerador(res.ast, res.tabela).gerar(origem)
```

Essa condição é a fronteira que impede gerar C depois de um erro semântico.
`Resultado.sucesso` significa ausência de diagnósticos de nível erro; não
significa que GCC compilou, que o programa executou ou que uma imagem foi vista.

### Arquivos e processos

| Arquivo / função | Parâmetros | Retorno/efeito | Exemplo e ligação |
|---|---|---|---|
| `cli.principal` | argv opcional | Código de saída inteiro | Lê argumentos, chama transpilar, grava C e pode compilar |
| `cli.compilar_e_executar` | arq_c, saída, bool executar | Código de saída | Encaminha ao executor |
| `executor.achar_compilador_c` | nenhum | Path ou None | Procura CC/portátil/PATH |
| `executor.compilar` | Path do C | bool, log, Path ou None | Compila com runtime e include |
| `executor.executar` | exe, cwd, limite_s | int, string | Captura stdout/stderr do desenho |
| `pipeline.executar_programa` | texto, pasta_saida, nome_base, área | `ResultadoExecucao` | Salva fonte/C, compila, executa e prepara PNG |
| `pipeline.etapas` | resultado ou None | Lista `(nome, estado)` | `erro` semântico deixa Gerar C pendente |
| `pipeline.diagnostico_ambiente` | nenhum | String de informações | Mostra caminhos, recursos e compilador |
| `pipeline.autoteste` | nenhum | `(bool, texto)` | Usa casa.td em pasta temporária, removida no fim |

`ResultadoExecucao` guarda `transp`, arquivos, compilou/executou, logs,
PPM/PNG, dimensões, ampliação e indicação de compilador ausente. `compilou=None`
significa etapa não tentada, enquanto `False` significa tentativa/falta do
recurso com falha. A UI usa essa diferença para não pintar tudo como erro.

### Imagem e runtime

| Função | Entrada | Retorno/efeito | Exemplo |
|---|---|---|---|
| `imagem.ler_ppm` | bytes do P6 | w,h,RGB | Header 6 4 → raster de 72 bytes |
| `imagem.rgb_para_png` | w,h,RGB,fator | bytes PNG | 6 × 4 com fator 10 → 60 × 40 |
| `imagem.ppm_para_png` | PPM,fator | PNG,w,h originais | Conveniência para converter |
| `imagem.converter_arquivo` | origem,destino,fator | w,h e arquivo escrito | Usada pela ferramenta CLI |
| `imagem.fator_para_caber` | dimensões e limites | inteiro >=1 | Escolhe ampliação da prévia |
| `td_criar` | largura,altura | TDCanvas* ou NULL | Aloca grade branca |
| `td_definir_cor` | canvas,nome,RGB,símbolo | índice ou −1 | Acrescenta cor na paleta |
| `td_usar` | canvas,índice | Atualiza cor ativa | Chamado após `usar` |
| `td_ponto` | canvas,x,y | Escreve índice | Sobrescreve o pixel |
| `td_linha` | canvas,x1,y1,x2,y2 | Escreve segmento ortogonal | Extremos incluídos |
| `td_retangulo` | canvas,x,y,w,h | Desenha quatro lados | Sem preenchimento |
| `td_salvar` | canvas,nome de arquivo | 0 sucesso, 1 falha | Resolve índices em RGB e grava P6 |
| `td_imprimir_ascii` | canvas | stdout | Legenda e grade; omite grade se largura >120 |
| `td_liberar` | canvas | Libera alocações | Aceita NULL |

### Assistentes, GUI e suporte

| Função/classe | Entrada | Saída/efeito e relação |
|---|---|---|
| `assistente.gerar` | pedido,progresso | `ResultadoGeracao`; valida pedido vazio e chama o gerador local |
| `assistente_local.normalizar` | texto | Texto minúsculo, sem marcas de acento |
| `assistente_local.Figura` | tipo e atributos | Modelo temporário do pedido, não nó da AST TinyDraw |
| `assistente_local.interpretar` | pedido | `(codigo_td, notas)` ou ErroAssistente |
| `assistente_local._layout` | figuras,tela,notas | W,H e figuras posicionadas/ajustadas |
| `assistente_local.Emissor` | chamadas de figuras | Acumula declarações e corpo `.td` |
| `assistente_local.gerar_local` | pedido,callback de progresso | Fonte + validade + log após transpilar |
| `gui.App` | sem parâmetros públicos adicionais | Janela com estado de editor, fila e resultado |
| `App.acao_gerar` | campos da UI | Inicia assistente e, ao concluir, execução |
| `App.acao_executar` | texto do editor | Inicia pipeline em thread |
| `App._mostrar_resultado` | ResultadoExecucao | Atualiza prévia, C, diagnósticos e tags |
| `App.acao_salvar_imagem` | escolha em diálogo | Copia PNG ampliado ou PPM original |
| `caminhos.pasta_runtime/pasta_exemplos` | nenhum | Paths no fonte ou em `_MEIPASS` |
| `caminhos.pasta_saida_padrao` | nenhum | Pasta de saída do usuário |
| `tinydraw_studio.main` | sys.argv | UI ou autoteste com retorno inteiro |

As funções internas de reconhecimento do assistente (_medidas, _posicao,
_criar_figura) usam regex sobre pedaços da frase. Seus resultados não dispensam
a validação da fonte emitida. A fachada retorna `ResultadoGeracao`, enquanto o
compilador retorna `Resultado` e o pipeline retorna `ResultadoExecucao`: são
objetos distintos de três níveis de responsabilidade.

## Parte 10 — Execução completa de um exemplo

### Fonte escolhida

Use `exemplos/validos/estudo.td`, exatamente:

```text
tela 6 por 4
cor VERMELHO = 255, 0, 0
cor AZUL = 0, 0, 255
usar VERMELHO
retangulo em 1, 1 tamanho 4 por 3
linha de 0, 0 ate 5, 0
usar AZUL
linha de 5, 0 ate 5, 3
ponto em 1, 1
salvar "estudo.ppm"
```

O exemplo usa todos os tipos de comando, duas cores, linha horizontal, vertical,
contorno e sobreposição. É pequeno o suficiente para conferir pixel a pixel.

### Tokens reais e como reproduzi-los

```powershell
py ferramentas/rastrear_exemplo.py
Get-Content build/estudo/tokens.txt
Get-Content build/estudo/ast.txt
Get-Content build/estudo/tabela.txt
Get-Content build/estudo/estudo.c
```

A ferramenta chama o transpilador real e grava artefatos de análise. Não compila
nem simula uma imagem. Os tipos e valores por linha são:

```text
1: TELA INT(6) POR INT(4)
2: COR ID(VERMELHO) IGUAL INT(255) VIRGULA INT(0) VIRGULA INT(0)
3: COR ID(AZUL) IGUAL INT(0) VIRGULA INT(0) VIRGULA INT(255)
4: USAR ID(VERMELHO)
5: RETANGULO EM INT(1) VIRGULA INT(1) TAMANHO INT(4) POR INT(3)
6: LINHA DE INT(0) VIRGULA INT(0) ATE INT(5) VIRGULA INT(0)
7: USAR ID(AZUL)
8: LINHA DE INT(5) VIRGULA INT(0) ATE INT(5) VIRGULA INT(3)
9: PONTO EM INT(1) VIRGULA INT(1)
10: SALVAR STRING(estudo.ppm)
11: EOF
```

Há 59 tokens incluindo EOF. As posições completas estão em `tokens.txt`.
Na primeira linha: TELA em 1:1, INT 6 em 1:6, POR em 1:8, INT 4 em 1:12.
EOF está em 11:1 porque o arquivo termina com uma quebra de linha.

### AST e estado semântico

`descrever` mostra uma raiz Programa com os seguintes nós, na ordem:

```text
Tela(largura=6, altura=4)
DefCor(nome='VERMELHO', r=255, g=0, b=0)
DefCor(nome='AZUL', r=0, g=0, b=255)
Usar(nome='VERMELHO')
Retangulo(x=1, y=1, largura=4, altura=3)
Linha(x1=0, y1=0, x2=5, y2=0)
Usar(nome='AZUL')
Linha(x1=5, y1=0, x2=5, y2=3)
Ponto(x=1, y=1)
Salvar(arquivo='estudo.ppm')
```

A ferramenta acrescenta as localizações reais ao mostrar os nós.

| Após linha | Tabela/estado e verificação |
|---|---|
| 1 | dim=(6,4), tela declarada e válida |
| 2 | VERMELHO: RGB=(255,0,0), índice 1, usada=False |
| 3 | AZUL: RGB=(0,0,255), índice 2, usada=False |
| 4 | cor ativa VERMELHO; usada=True |
| 5 | Canto (1,1), oposto (4,3): dentro; tamanho positivo |
| 6 | Extremos (0,0),(5,0) válidos, mesmo y |
| 7 | cor ativa AZUL; usada=True |
| 8 | Extremos (5,0),(5,3) válidos, mesmo x |
| 9 | Ponto (1,1) dentro; cor ativa azul |
| 10 | Nome permitido; salvo=True; nenhum comando posterior |

O resultado de análise esperado e verificável é sucesso sem avisos. Nenhuma
regra compara pixels nesse momento; o analisador só valida as operações.

### C correspondente

Trechos efetivamente emitidos, omitindo os `printf` de rastreamento:

```c
TDCanvas *c = td_criar(6, 4);
int cor_1 = td_definir_cor(c, "VERMELHO", 255, 0, 0, 'V');
int cor_2 = td_definir_cor(c, "AZUL", 0, 0, 255, 'A');
td_usar(c, cor_1);
td_retangulo(c, 1, 1, 4, 3);
td_linha(c, 0, 0, 5, 0);
td_usar(c, cor_2);
td_linha(c, 5, 0, 5, 3);
td_ponto(c, 1, 1);
```

Depois vem `td_salvar(c, "estudo.ppm")` com tratamento de falha, impressão
ASCII e liberação da memória. O arquivo completo inclui `main` e verificação
da alocação; esses trechos isolados não são um programa C completo.

### Compilar, executar e conferir

```powershell
py -m tinydraw exemplos/validos/estudo.td --executar -o build/estudo
py ferramentas/ppm_para_png.py build/estudo/estudo.ppm 40
Invoke-Item build/estudo/estudo.png
```

**Estado desta revisão:** a análise e a geração de C foram executadas; a
compilação, o executável e o PPM deste exemplo não foram produzidos neste
ambiente, que não tinha GCC/cc/clang. A sequência acima é a validação a realizar
no computador da apresentação. Não apresente a previsão abaixo como imagem
observada nesta revisão.

Previsão da grade final, onde V é vermelho, A azul e ponto é branco:

```text
      x=012345
y=0     VVVVVA
y=1     .AVVVA
y=2     .V..VA
y=3     .VVVVA
```

O pixel (5,0), antes vermelho pela horizontal, fica azul pela vertical posterior.
O pixel (1,1), inicialmente vermelho no canto do retângulo, fica azul pelo ponto
da linha 9. O interior (2,2) permanece branco. O retângulo termina em (4,3),
então a coluna 5 é azul exclusivamente pela vertical.

| Coordenada | RGB previsto | Justificativa |
|---|---|---|
| (0,0) | (255,0,0) | Horizontal vermelha |
| (5,0) | (0,0,255) | Vertical azul sobre a horizontal |
| (1,1) | (0,0,255) | Último ponto sobre o contorno |
| (2,2) | (255,255,255) | Interior não preenchido |
| (4,3) | (255,0,0) | Borda inferior vermelha |
| (5,3) | (0,0,255) | Último pixel da vertical |

Para conferir os pixels reais, depois da execução:

```powershell
py -c "from pathlib import Path; from tinydraw.imagem import ler_ppm; w,h,rgb=ler_ppm(Path('build/estudo/estudo.ppm').read_bytes()); print(w,h); print(tuple(rgb[(1*w+1)*3:(1*w+1)*3+3])); print(tuple(rgb[(2*w+2)*3:(2*w+2)*3+3]))"
```

Deve imprimir dimensões 6 4, azul em (1,1) e branco em (2,2). Completem a
conferência das outras posições e comparem o log com as linhas da fonte.

**Mudança para demonstrar compreensão:** troque apenas `ponto em 1, 1` por
`ponto em 2, 2`. Antes de executar, preveja que (1,1) volta a vermelho e
(2,2) fica azul. Mostre a mudança no `.td`, no nó Ponto, no C e na imagem.

## Parte 11 — Perguntas para apresentação oral

Respondam primeiro sem ler. Uma resposta completa deve ligar conceito, nome
real do módulo e um exemplo. As perguntas difíceis ajudam a identificar o que
a implementação garante e o que permanece como limitação.

### Fundamentos e reconhecimento

**1. O que é uma DSL?**
É uma linguagem projetada para um domínio restrito. Sua sintaxe expressa
diretamente operações desse domínio. Aqui o domínio é desenhar com tela,
cores e formas simples; não é oferecer computação de propósito geral.

**2. Por que TinyDraw é uma DSL?**
Porque seus comandos e regras tratam especificamente de desenho. A gramática
não oferece expressões gerais ou funções. A justificativa está na redução de
detalhes de C para uma descrição pequena e validável de figuras.

**3. Por que usar palavras reservadas em português?**
É uma exigência do DAC e aproxima a descrição do público escolhido. A
implementação reconhece nomes específicos em minúsculas; não entende qualquer
frase em português dentro de um arquivo `.td`.

**4. Qual a diferença entre léxico e sintaxe?**
O léxico transforma caracteres em categorias: `6` vira INT. A sintaxe verifica
se essas categorias estão na ordem da gramática: depois de `tela INT` vem POR.
`@` falha no léxico; `tela 6 4` falha na sintaxe.

**5. O que acontece com um caractere inválido?**
O lexer gera um diagnóstico posicionado e continua procurando outros erros.
O orquestrador detecta a lista de erros e não chama o parser. Não há geração
de C a partir dessa fonte no resultado atual.

**6. `TELA 6 por 4` tem erro léxico?**
Não por causa de TELA: ela é um ID válido. O parser rejeita esse ID como início
de comando. Isso demonstra a diferença entre reconhecer uma palavra e reconhecer
uma palavra reservada específica.

**7. Por que `-1` não chega como número negativo à semântica?**
A regex de inteiro só aceita dígitos e o sinal `-` vira caractere inesperado.
É uma decisão da especificação léxica. Zero, por outro lado, é reconhecido e
pode ser rejeitado depois por regras de dimensões positivas.

**8. O que são BNF e EBNF?**
São notações de gramática. EBNF facilita escrever repetição e opcionalidade.
`programa = { comando } EOF` permite uma sequência de comandos; as chaves
representam repetição na documentação e não existem no arquivo TinyDraw.

**9. Como o parser escolhe uma regra?**
Consulta o tipo do token atual e usa um dicionário de métodos em `_comando`.
Os sete comandos começam por tokens distintos. Isso permite a decisão com
um token de antecipação, sem retroceder.

**10. Qual é a função da AST?**
Guardar a estrutura útil do programa para as próximas fases. Um ponto fica
com x,y e posição na fonte, sem precisar guardar a palavra `em` ou a vírgula.
Semântica e gerador trabalham com esses nós, sem reparsar o texto.

**11. AST é sempre uma árvore profunda?**
Não. Aqui a raiz contém uma lista de comandos com campos escalares. Não há
expressões aninhadas. A estrutura é simples porque a linguagem é simples.

**12. A AST é imutável?**
Não por imposição das classes: seus nós são dataclasses mutáveis. As fases
seguintes consultam seus dados sem transformá-los. Os tokens, em contraste,
usam `frozen=True`.

### Semântica e contexto

**13. Como funciona a tabela de símbolos?**
É um dicionário que associa o nome da cor ao objeto Simbolo com RGB, índice,
linha de declaração e indicador de seleção. Declarações inserem; `usar` busca;
o gerador consulta a lista para a legenda.

**14. O que acontece quando uma cor não existe?**
`buscar` retorna None e `_usar` registra erro semântico. O comando é
sintaticamente válido, mas sua referência não pode ser resolvida. O erro
impede C, independentemente das outras partes válidas.

**15. Por que a ordem das declarações importa?**
O analisador percorre a lista sequencialmente. Uma cor só está na tabela
depois de sua declaração. Não há uma passagem anterior que registre todos os
nomes para permitir referências futuras.

**16. A tela precisa ser o primeiro comando?**
Os exemplos usam essa convenção, mas o analisador permite cor e usar antes
da tela. Ele exige tela antes de desenho/salvar e apenas uma declaração.
Essa distinção deve ser explicada com o código, sem prometer uma regra ausente.

**17. Como se valida um retângulo inteiro?**
Testa tamanho positivo, canto inicial dentro e canto oposto x+w−1,y+h−1.
Como as coordenadas crescem para direita/baixo e dimensões são positivas,
essas verificações bastam para as quatro bordas caberem.

**18. Por que a coordenada máxima é largura−1?**
Os índices começam em zero. Há largura posições, de 0 a largura−1. O valor
largura seria a próxima posição, já fora da linha lógica de pixels.

**19. Qual a diferença entre erro e aviso?**
Erro bloqueia a geração. Aviso indica uma situação aceita, como uma linha
degenerada ou cor nunca selecionada. Um aviso não faz a propriedade sucesso
ficar falsa.

**20. Selecionar uma cor prova que ela aparece no resultado?**
Não. `usada` indica seleção com `usar`. Pode não haver desenho ou todos os
pixels daquela cor podem ser sobrescritos depois. Não há análise de visibilidade
final de cada cor.

**21. Por que não recortar figuras fora da tela?**
A regra desta DSL é rejeitar, permitindo encontrar um erro na fonte antes de
executar. O runtime tem verificações defensivas, mas elas não são um recurso
de recorte aceito pela linguagem.

**22. Por que pode existir uma cor inválida na tabela?**
O analisador acumula diagnósticos e continua para oferecer mais informação.
Isso é seguro neste fluxo porque `transpilar` só chama o gerador sem erros.
O contrato é analisar, checar diagnósticos e então gerar.

### C, memória e formatos

**23. Por que gerar C?**
Porque é o alvo exigido e torna verificável a tradução para uma linguagem
geral. Cada comando vira uma chamada explícita ao runtime; GCC produz o
programa que efetivamente grava os pixels.

**24. O que GCC faz que o transpilador não faz?**
GCC entende C, compila suas unidades, resolve a ligação com as implementações
e produz executável nativo. O transpilador entende TinyDraw e suas regras de
domínio. São validações e traduções em níveis diferentes.

**25. Por que passar também `runtime/tinydraw.c` ao compilador?**
O cabeçalho declara as funções, mas não contém suas implementações. Sem o
arquivo C do runtime, as chamadas `td_*` do programa gerado ficariam sem
definição na etapa de ligação.

**26. Como um pixel é armazenado?**
Como um byte que indexa a paleta, na posição y×largura+x. RGB só é resolvido
quando necessário, por exemplo ao salvar. Não é um vetor de trios RGB na
memória do canvas.

**27. Por que até 255 cores declaradas?**
Há 256 índices representáveis num byte. Um é reservado ao fundo branco.
Os demais 255 podem ser associados às declarações da DSL. Isso é diferente
de dizer que RGB só pode representar 255 cores.

**28. Como funciona a sobreposição?**
A atribuição em `td_ponto` substitui o índice antigo. Como linha e retângulo
usam pontos, todas as formas seguem a mesma regra. O último comando que
atingir uma coordenada vence, sem misturar cores.

**29. Como é desenhado um retângulo sem preenchimento?**
São quatro chamadas de linha. Há escrita nas bordas e nenhuma varredura do
interior. Para provar isso, confira um pixel interior branco no PPM.

**30. Como funciona o formato PPM desta implementação?**
É P6: identificador, dimensões e máximo 255 no cabeçalho textual, seguidos
de bytes RGB. Não são números decimais separados por espaços no raster.
P3 seria outra variante, não a produzida aqui.

**31. Por que um raster 6 × 4 tem 72 bytes?**
São 24 pixels, cada um com 3 canais de um byte: 6×4×3=72. Isso é só o raster;
o arquivo total também tem os bytes do cabeçalho.

**32. PNG é produzido pelo C?**
Não. O C produz PPM e o Python lê RGB e escreve PNG com zlib e blocos PNG.
É uma conversão opcional para facilitar visualização/exportação.

**33. Como demonstrar que a imagem corresponde ao `.td`?**
Use o exemplo pequeno, preveja pixels, mostre tokens/AST, localize suas
chamadas C, execute e confira coordenadas no PPM. Altere uma coordenada na
hora e repita. O log é apoio, não prova única da imagem.

**34. Se o C compila sem avisos, o compilador TinyDraw está correto?**
Isso só prova parte do caminho. É possível gerar uma chamada C com coordenada
errada que ainda compila. Os testes de pixels e sobreposição procuram falhas
semânticas da tradução que o compilador C não detectaria.

### Studio e perguntas difíceis

**35. O assistente local desenha diretamente?**
Não. Ele fornece texto TinyDraw. A fonte passa pelo léxico, parser, semântica,
gerador e executor. A imagem só existe depois da execução do C.

**36. O assistente local é uma rede neural?**
Não. É um conjunto de regex, regras geométricas e modelos de composição.
Ele reconhece frases limitadas e emite comandos. Essa explicação permite
justificar por que certas frases não são entendidas.

**37. Como existem círculos no assistente se a DSL não tem círculo?**
O assistente aproxima um disco com segmentos horizontais de larguras
variáveis. O `.td` resultante só contém ponto/linha e outros comandos básicos.
Não foi adicionada uma produção `circulo` à gramática.

**38. Aceitar o `.td` do assistente prova que ele entendeu o pedido?**
Não. O compilador prova conformidade com as regras implementadas. O assistente pode
gerar um desenho válido diferente do pedido. Conferir a intenção e o resultado
continua sendo uma atividade humana.

**39. Por que usar thread e queue no Studio?**
Para tarefas lentas não bloquearem o loop de eventos. A thread trabalha e
coloca dados na fila; `_poll` atualiza widgets na thread Tk. Isso preserva
a interação e evita acesso indevido aos widgets em segundo plano.

**40. Por que o `.exe` Studio ainda precisa de GCC?**
PyInstaller empacota o aplicativo Python e recursos, mas cada novo desenho
ainda exige compilar o C recém-gerado. Não se trata apenas de executar um
desenho fixo previamente compilado.

**41. O que significa um teste pulado?**
Significa que sua condição de execução não foi atendida. Não é uma aprovação.
Sem compilador, testes de ponta a ponta não verificam o PPM. O relatório
precisa separar aprovação de testes e etapas não executadas.

**42. Por que não manter sempre a imagem anterior na tela?**
Ela pode ser confundida com o resultado da fonte atual. `_mostrar_resultado`
limpa a prévia ao processar o resultado atual, e o pipeline remove um PPM
antigo antes de uma nova compilação válida. Arquivos antigos em disco ainda
devem ser identificados como antigos.

**43. O runtime é seguro para qualquer chamada C manual?**
Não foi projetado nem validado como biblioteca genérica para entradas
arbitrárias. Seu contrato normal é receber dados que passaram pela semântica.
O ponto verifica limites, mas nem toda função verifica ponteiros e valores
independentes. Explique essa fronteira em vez de prometer segurança universal.

**44. A complexidade da análise toda é estritamente O(n)?**
O scanner/parser seguem uma passagem sobre a fonte/tokens e comandos, e o
dicionário oferece busca média constante. Mas `todas()` copia a lista de cores
e a semântica o chama em declarações, podendo acumular trabalho quadrático
no número de cores. Como há limite 255, esse custo é limitado no domínio.
Além disso há ordenação de diagnósticos e custo de montagem do C.

**45. Como adicionar uma diagonal nativa corretamente?**
Não bastaria remover o erro de `_linha`: o runtime não a desenha. Seria
necessário decidir a semântica/rasterização, implementar algoritmo como
Bresenham, testar inclinações e extremos e atualizar documentação. Essa
evolução não foi feita nesta revisão.

**46. Como adicionar um comando novo?**
Defina propósito e regra formal; acrescente reservada, nó AST, produção do
parser, validação, geração e suporte runtime quando necessário. Escreva
casos válidos/ inválidos e confira pixels. Alterar só a ajuda não implementa
uma construção de linguagem.

**47. Um nome `%s.ppm` vira instrução de C?**
Não pelo mecanismo de impressão: o nome é um argumento de `%s`, não a string
de formato. Strings são escapadas, e caminhos/nomes Windows inválidos são
rejeitados. Não use isso para afirmar que toda entrada arbitrária está
formalmente provada segura.

**48. Por que o assistente não altera o desenho atual automaticamente?**
Cada pedido gera um novo programa por regras locais. Para alterar um desenho já
existente, edite o `.td` no editor e execute novamente. Isso mantém observável a
relação entre os comandos escritos e a imagem.

**49. Como declarar o uso de IA sem inventar autoria?**
Registre ferramentas e finalidades reais, identifique os arquivos e relate
o que cada estudante de fato conferiu. Esta revisão por Codex está registrada.
Não atribua automaticamente aos integrantes as verificações feitas pelo agente
nem confirme histórico apenas porque um texto antigo o mencionava.

**50. Quais são os limites atuais mais relevantes?**
DSL sem expressões/laços e sem figuras curvas nativas; parser sem recuperação;
tela e paleta limitadas; leitor PPM restrito; assistente local limitado a regras;
GCC necessário. Nesta revisão também restam validações
de compilação C, imagem de ponta a ponta e pacote Windows.

## Parte 12 — Roteiro prático de demonstração e estudo

### Preparação no computador da apresentação

Extraia a pasta completa. Abra PowerShell na raiz. Use `Get-Location` e
`Get-ChildItem` para confirmar que vê `README.md`, `tinydraw/` e `runtime/`.
Não dependa de rede para a demonstração do núcleo.

```powershell
py --version
gcc --version
py -m tkinter
py -m unittest discover -v
```

Feche a janela de teste do Tkinter. Confirme os testes pulados e a causa.
Execute o teste completo da GUI em uma sessão de teste separada:

```powershell
$env:TINYDRAW_TESTE_GUI = '1'
py -m unittest tests.test_gui_smoke -v
Remove-Item Env:TINYDRAW_TESTE_GUI
```

O teste de GUI existente deve ser executado em processo separado: ele ajusta
HOME/USERPROFILE internamente. Não reutilize esse processo como sessão pessoal.
Depois confira a pasta de saída e exportação manualmente.

### Demonstração sugerida, cerca de 12 a 15 minutos

| Tempo aproximado | Ação concreta | Explicação/evidência |
|---|---|---|
| 0–1 min | Apresente problema e fluxo | Descrição `.td`, validação, C, executável e PPM |
| 1–3 min | `py tinydraw_studio.py`, abra estudo.td em Arquivo | Fonte editável e comandos em português |
| 3–4 min | Execute F5 | Imagem, barra de etapas, log e C gerado |
| 4–6 min | Rode comandos de tokens/AST no terminal | Relacione nó Retangulo e campos com a fonte |
| 6–8 min | Mostre C e biblioteca | `td_retangulo`, quatro linhas, índice y×W+x |
| 8–10 min | Rode três exemplos inválidos | Identifique fase e regra específica de cada erro |
| 10–12 min | Altere o ponto de (1,1) para (2,2), execute | Preveja e confira os dois pixels alterados |
| 12–13 min | Mostre assistente local, se houver tempo | Ele escreve `.td`; não substitui o compilador |
| 13–15 min | Limites e declaração de IA | Registros reais e verificações da equipe |

Todos devem saber executar e explicar cada ação. Os tempos são uma sugestão de
ensaio, não divisão histórica de participação.

### Comandos do núcleo para copiar durante o ensaio

```powershell
py ferramentas/rastrear_exemplo.py
py -m tinydraw exemplos/validos/estudo.td --tokens --ast --so-c -o build/estudo
Get-Content build/estudo/estudo.c
py -m tinydraw exemplos/validos/estudo.td --executar -o build/estudo
py ferramentas/ppm_para_png.py build/estudo/estudo.ppm 40
Invoke-Item build/estudo/estudo.png
```

Mostre no `.c` `td_criar`, `td_definir_cor`, `td_retangulo`, `td_linha`,
`td_ponto` e `td_salvar`. Abra `runtime/tinydraw.c` e localize a atribuição de
pixel e as quatro chamadas de linha. Compare a imagem com a grade prevista.

### Erros separados e reproduzíveis

Use os arquivos inválidos existentes para mostrar múltiplos diagnósticos:

```powershell
py -m tinydraw exemplos/invalidos/erro_lexico.td --tokens --so-c
py -m tinydraw exemplos/invalidos/erro_sintatico.td --tokens --ast --so-c
py -m tinydraw exemplos/invalidos/erro_semantico.td --tokens --ast --so-c
```

Para isolar um erro por vez, crie os três arquivos em UTF-8 sem BOM:

```powershell
py -c "from pathlib import Path; p=Path('build/demo-erros'); p.mkdir(parents=True,exist_ok=True); fontes={'lexico':'tela 6 por 4 @','sintatico':'tela 6 4','semantico':'tela 6 por 4 usar AUSENTE salvar '+chr(34)+'erro.ppm'+chr(34)}; [(p.joinpath(n+'.td').write_text(t,encoding='utf-8')) for n,t in fontes.items()]"
py -m tinydraw build/demo-erros/lexico.td --so-c -o build/demo-erros/saida-lexico
py -m tinydraw build/demo-erros/sintatico.td --so-c -o build/demo-erros/saida-sintatico
py -m tinydraw build/demo-erros/semantico.td --so-c -o build/demo-erros/saida-semantico
```

O primeiro arquivo aponta `@`; o segundo aponta falta de `por`; o terceiro
aponta cor não declarada. Evite criar fontes com BOM: o lexer atual não ignora
esse marcador, que também seria diagnosticado como caractere inesperado.
O Windows PowerShell 5.1 inclui BOM em `Set-Content -Encoding utf8`; o comando
Python acima evita essa diferença de ambiente.

As pastas de saída precisam estar vazias ou ainda não existir. Os erros devem
impedir gerar C novo. Não aponte arquivos de tentativas anteriores como resultado
dessa execução. O exemplo léxico falha antes da AST; o sintático também não
retorna AST completa; o semântico retorna AST, mas não C.

### Demonstração pelo Studio

1. Abra `exemplos/validos/estudo.td` em **Arquivo → Abrir programa .td**.
2. Execute F5. Mostre a imagem, C e log. Explique a cor ativa e sobreposição.
3. Troque o ponto para (2,2), preveja o efeito e execute novamente.
4. Exporte PNG e PPM em **Salvar imagem** e abra o PNG salvo.
5. Abra cada exemplo inválido pelo menu Exemplos, execute e explique a aba
   Diagnósticos e as linhas marcadas. Retorne ao válido antes de continuar.
6. Peça um quadrado vermelho no assistente local e mostre o `.td` produzido.
7. Mostre a barra do mesmo compilador sendo usada no código gerado pelo assistente.

Tokens e AST são demonstrados pela CLI/ferramenta; a interface atual não tem
abas próprias para essas estruturas. Não procure botões que não existem.

### Exercícios para apropriação individual

| Exercício | Previsão antes de executar | O que localizar no código |
|---|---|---|
| Inverter os extremos da linha horizontal | Mesmos pixels | min/max e laço inclusivo em td_linha |
| Trocar a ordem das linhas vermelha e azul mantendo seleções corretas | Cor da interseção muda | Estado de cor e última escrita |
| Colocar ponto em (6,0) na tela 6×4 | Erro semântico | `_dentro` |
| Remover `por` | Erro sintático | `_tela` e `_consumir` |
| Inserir `@` | Erro léxico | DESCONHECIDO em ESPECIFICACAO |
| Declarar duas cores com mesmo nome | Erro semântico | declarar/buscar na tabela |
| Selecionar uma cor e não desenhar | Sem aviso de não selecionada | `s.usada=True` em `_usar` |
| Retângulo de 1×1 | Um pixel final | Lados coincidentes no runtime |
| Linha de um ponto para ele mesmo | Aviso e pixel desenhado | `_linha` e ramo horizontal C |
| Pedir retângulo preenchido no assistente | Várias linhas no `.td` | Emissor.cheio |

Para cada exercício, registrem o resultado que de fato observaram, a explicação
e uma dúvida que precisou ser investigada. Não preencham como concluído antes
de realizar. Um colega pode solicitar uma pequena alteração que não esteja na
tabela; quem demonstra deve descobrir a regra em vez de recorrer a uma fala pronta.

### Ensaio final com troca de papéis

Façam três rodadas. Em cada uma, uma pessoa explica, outra opera e outra
questiona. Na rodada seguinte, troquem. Em todas, cada pessoa deve explicar ao
menos um caso de cada fase e uma correspondência de pixels. Se alguém conhece
só “sua parte”, retomem o fluxo completo antes de apresentar.

Antes da entrega, preencham o memorial e o uso real de IA, leiam o relatório
de limitações e executem as pendências de GCC e empacotamento no ambiente final.
Não apresentem como verificado o que foi apenas previsto por este guia.
