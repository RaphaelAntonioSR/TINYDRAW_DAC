# TinyDraw

TinyDraw é uma linguagem de domínio específico (DSL), com comandos em português,
para descrever pontos, linhas e retângulos. O transpilador em Python valida a
fonte e gera C. O programa compilado produz uma imagem PPM e uma representação
em ASCII. O objetivo acadêmico é tornar observáveis as etapas de compilação e
comparar a descrição do desenho com o comportamento do código gerado.

Projeto da proposta 8 do catálogo MiniLinguagens, para o DAC do 8º semestre de
Engenharia de Computação.

**Equipe:** Antonio Marcos dos Santos Junior, Fernando Augusto da Silva e
Raphael Antonio dos Santos Rangel.

## Comece por aqui

Na pasta do projeto, com Python e GCC configurados:

```powershell
py -m unittest discover -v
py -m tinydraw exemplos/validos/casa.td --executar
py ferramentas/ppm_para_png.py build/casa.ppm 12
Invoke-Item build/casa.png
py tinydraw_studio.py
```

Para preparar a defesa oral, leia [o guia de estudos](docs/GUIA_DE_ESTUDOS.md).
Ele acompanha o código real, contém perguntas explicadas, exercícios e roteiro
de demonstração. O edital prevê nota zero quando a verificação de autoria ou de
apropriação for insuficiente. Ler o guia não substitui executar, alterar e
explicar o projeto individualmente.

## Problema e linguagem

Desenhar diretamente em C exige lidar com memória, índices e formato de arquivo.
TinyDraw concentra a descrição nas figuras e detecta erros de domínio antes de
gerar C: cor não declarada, RGB inválido, coordenada fora da tela e diagonal.

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

Esse programa está em `exemplos/validos/estudo.td`. A origem é o canto superior
esquerdo: x cresce para a direita e y para baixo. O fundo é branco. O último
comando que escreve em um pixel determina sua cor. Retângulos têm só contorno;
os extremos das linhas são incluídos. Comentários começam com `#`.

Palavras reservadas são minúsculas; identificadores distinguem maiúsculas e
minúsculas. `até` e `retângulo` também são aceitos. Números são inteiros sem sinal.
Quebras de linha não fazem parte da gramática. Declare uma tela antes de desenhar
ou salvar, cores antes de selecioná-las, e selecione uma cor antes de desenhar.
`salvar` encerra o programa.

## Arquitetura e escopo

```text
arquivo .td → lexer → tokens → parser → AST → semântica/tabela → gerador → C
                                                                         ↓
                                            PPM + ASCII ← executável ← GCC
```

O lexer reconhece unidades textuais. O parser verifica a sequência e constrói a
AST. A semântica confere regras de contexto e limites. Só uma fonte sem erros
chega ao gerador. `executor.py` chama o compilador C e o executável, sem shell.
`runtime/tinydraw.c` mantém os pixels e grava a imagem.

O núcleo da DAC inclui tela colorida, cores nomeadas, seleção de cor, ponto,
linha horizontal ou vertical, contorno de retângulo, sobreposição, PPM e todas as
etapas do transpilador. Os exemplos demonstram duas ou mais cores; essa quantidade
não é um mínimo imposto a todo programa pelo analisador.

Studio, PNG e assistentes são extensões. Os assistentes escrevem texto `.td`;
o mesmo transpilador valida esse texto. Eles não produzem a imagem diretamente.

```text
tinydraw/
  lexer.py, parser.py, ast_nodes.py     reconhecimento e AST
  semantica.py, codegen.py              validação e emissão C
  compilador.py, erros.py               Interface interna e diagnósticos
  cli.py, __main__.py, executor.py      arquivos, compilação e execução
  gui.py, pipeline.py                   Studio e fluxo até a prévia
  assistente.py, assistente_local.py
  imagem.py, caminhos.py                PNG e localização de recursos
runtime/                               biblioteca C e cabeçalho
exemplos/validos/, exemplos/invalidos/  demonstrações
tests/                                 testes unittest
ferramentas/                            PNG e rastreamento para estudo
docs/                                  especificação, guia e relatório
tinydraw_studio.py                      entrada do Studio/PyInstaller
executar_studio.bat, construir_exe.bat  atalhos Windows
```

## Dependências e instalação no Windows

O projeto usa a biblioteca padrão do Python, incluindo `re`, `dataclasses`,
`subprocess`, `tkinter`, `struct` e `zlib`. A referência desta revisão
é Python 3.12.14; não foi certificada uma matriz de versões. PyInstaller é
necessário apenas para empacotar. O GCC precisa aceitar C99.

1. Extraia o projeto em uma pasta em que possa gravar.
2. Instale o Python para Windows a partir de [python.org](https://www.python.org/downloads/windows/),
   com launcher `py` e Tcl/Tk. Reabra o terminal.
3. Instale uma distribuição GCC para Windows, como MinGW-w64/WinLibs. Adicione a
   pasta que contém `gcc.exe` ao PATH e reabra o terminal. A distribuição precisa
   dos seus arquivos de suporte; copiar apenas `gcc.exe` não basta.
4. Entre na pasta deste README e confira:

```powershell
py --version
py -m tkinter
gcc --version
```

Feche a janela de teste do Tkinter. Se `py` não existir, ajuste a instalação ou
use o caminho absoluto de um Python instalado. Os `.bat` dependem de `py`.
O executor também procura `cc` e `clang`. Na validação final foi usado GCC 16.2.0 (MSYS2 UCRT64), com compilação,
execução e conferência de imagens. Veja [a validação final](docs/VALIDACAO_FINAL.md).

Se o GCC não estiver no PATH, informe um caminho **sem argumentos**:

```powershell
$env:CC = 'C:\Ferramentas\mingw64\bin\gcc.exe'
```

## Linha de comando e imagens

```powershell
py -m tinydraw exemplos/validos/casa.td --tokens --ast --so-c
py -m tinydraw exemplos/validos/casa.td --executar
py -m tinydraw exemplos/validos/sobreposicao.td --executar -o build/sobreposicao
py -m tinydraw exemplos/invalidos/erro_lexico.td --so-c
py -m tinydraw exemplos/invalidos/erro_sintatico.td --so-c
py -m tinydraw exemplos/invalidos/erro_semantico.td --so-c
```

`--so-c` gera C sem compilar; sem essa opção o padrão é gerar e compilar.
`--executar` também roda o binário. `--tokens` e `--ast` mostram as estruturas
que a análise conseguiu produzir. Erros de análise retornam código 1; falha de
compilação C retorna 2. Avisos não bloqueiam a geração.

O diretório padrão da CLI é `build/`, relativo à pasta atual. O nome do `.c` e do
executável vem da entrada. O nome do PPM vem de `salvar`, e a execução ocorre no
diretório de saída. Para `casa.td`, espere `build/casa.c`, `build/casa.exe` no
Windows e, se compilar e executar corretamente, `build/casa.ppm`.

```powershell
py ferramentas/ppm_para_png.py build/casa.ppm 12
Invoke-Item build/casa.png
py ferramentas/rastrear_exemplo.py
```

A conversão PNG não precisa de Pillow. O último comando grava tokens, AST,
tabela e C em `build/estudo/`; ele não compila nem fabrica uma imagem.

## TinyDraw Studio e assistentes

Abra com `py tinydraw_studio.py` ou `executar_studio.bat`. O exemplo `casa.td`
entra no editor. Pressione F5 ou **Executar código** para processá-lo. Para
gerar a partir de uma descrição, digite
“um quadrado vermelho de lado 5 em 2, 2” e use **Gerar desenho** ou Ctrl+Enter.

As abas mostram imagem, log/ASCII, diagnósticos, C e atividade do assistente.
Edite o `.td` para comparar resultados. **Arquivo** permite abrir/salvar programas
e exportar PNG ampliado ou PPM original. O Studio grava em
`%USERPROFILE%\TinyDrawStudio\saida`; **Abrir pasta de saída** localiza os arquivos.
**Ajuda → Diagnóstico do ambiente** executa um autoteste com a casa.

O assistente local usa regras e regex, sem rede. Reconhece figuras, algumas cores,
medidas e posições. Preenchimentos, discos e triângulos viram combinações dos
comandos básicos; não há palavras reservadas novas para essas figuras.
Ele pode ajustar posições/tamanhos ou descartar figuras e registra isso no log.
Não compreende linguagem natural arbitrária.

## Testes e empacotamento

```powershell
py -m unittest discover -v
$env:TINYDRAW_TESTE_GUI = '1'
py -m unittest tests.test_gui_smoke -v
Remove-Item Env:TINYDRAW_TESTE_GUI
```

Confira a quantidade de testes pulados: `OK` com `skipped` não comprova as etapas
que não executaram. O teste completo da interface exige Tkinter e compilador C.
O [relatório](docs/RELATORIO_REVISAO.md) registra resultados e limites do ambiente.

Para empacotar, execute `construir_exe.bat` ou estes comandos na raiz:

```powershell
py -m pip install pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name TinyDrawStudio --add-data "runtime;runtime" --add-data "exemplos;exemplos" tinydraw_studio.py
```

O resultado esperado é `dist/TinyDrawStudio.exe`. O pacote inclui os recursos C
e exemplos, mas **não inclui o GCC**. O destino precisa de GCC no PATH, de `CC`
configurada ou de uma distribuição em `dist/gcc/bin/gcc.exe`.
`caminhos.py` usa `_MEIPASS` para localizar recursos extraídos do pacote.

```powershell
.\dist\TinyDrawStudio.exe --autoteste
Get-Content .\autoteste.txt
```

Sem console, leia `autoteste.txt` na pasta de trabalho atual. Aguarde a conclusão
e confira que não é um arquivo antigo. O executável Windows não foi produzido
nem validado nesta revisão: PyInstaller estava ausente.

## Limitações e documentos

Tela até 1000 × 1000, até 255 cores declaradas e fundo branco reservado.
A DSL não tem negativos, expressões, variáveis, laços, funções, diagonais ou
círculos nativos. O parser para no primeiro erro sintático. A AST usa dataclasses
mutáveis; não há otimização. O leitor de imagem aceita o P6 específico do runtime,
sem comentários no cabeçalho e com máximo RGB 255. A prévia amplia pixels e usa
rolagem quando necessário; não reduz a escala abaixo de 1. A legenda ASCII pode
reutilizar símbolos se houver muitas cores, sem alterar os RGB do PPM.

Entrada inválida não gera C novo; arquivos anteriores podem continuar no diretório.
Use pastas limpas para demonstrar essa propriedade.

- [Especificação técnica](docs/DOCUMENTACAO.md): regex, EBNF e regras semânticas.
- [Guia de estudos](docs/GUIA_DE_ESTUDOS.md): explicação aprofundada e defesa oral.
- [Autoria e uso de IA](docs/AUTORIA_E_IA.md): declaração desta revisão e memorial a completar com fatos reais.
- [Relatório da revisão](docs/RELATORIO_REVISAO.md): mudanças, testes e pendências.

Preencham o memorial e as verificações pessoais antes da entrega. O material
recebido não permite atribuir responsabilidades históricas aos integrantes.

A validação mais recente, com GCC e interface completa, está em [VALIDACAO_FINAL.md](docs/VALIDACAO_FINAL.md). Fontes UTF-8 com BOM inicial também são aceitas.
