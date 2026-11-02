# Relatório de revisão do TinyDraw

Data: 02/11/2026. Trabalho realizado sobre o ZIP fornecido, preservando a
implementação existente. O arquivo original em Downloads não foi alterado.

## Resultado e limites

README reescrito, guia de estudos criado em doze partes com 50 perguntas
respondidas, código comentado em pontos relevantes e falhas de robustez corrigidas.
O compilador mantém o caminho `.td → análise → C → compilação → execução → PPM`.
Os assistentes continuam gerando somente fonte TinyDraw.

A suíte final descobriu **90 testes: 83 passaram e 7 foram pulados**, sem falhas.
A suíte original descobria 79: 72 passaram e os mesmos 7 foram pulados.
Os testes adicionais cobrem regressões concretas encontradas nesta revisão.
O teste parcial de interface, executado separadamente, também passou.

**Não há certificação de ponta a ponta:** nenhum GCC/cc/clang foi encontrado no
ambiente. C foi gerado, mas não compilado nesta revisão. Nenhum executável de
desenho ou PPM vindo do runtime C foi produzido aqui. PyInstaller não estava
instalado; `dist/TinyDrawStudio.exe` não foi construído nem validado.

## Ambiente e verificações reais

Windows, PowerShell, Python 3.12.14 do runtime disponibilizado ao agente, com
Tkinter funcional. O launcher `py` estava ausente no PATH. Os comandos Python
foram executados pelo caminho absoluto desse interpretador; os documentos
ensinam o uso de `py` no computador da equipe.

| Verificação | Resultado observado |
|---|---|
| Importação de todos os módulos Python do pacote | Passou |
| Léxico, parser, AST, semântica e geração C | Testes passaram |
| Quatro exemplos válidos, incluindo estudo.td | Aceitos, sem erros nem avisos |
| Três exemplos inválidos | Rejeitados na fase esperada, sem código C no resultado |
| Exemplo inválido léxico | 3 erros |
| Exemplo inválido sintático | 1 erro |
| Exemplo inválido semântico | 12 erros e 2 avisos |
| Rastreamento estudo.td | 59 tokens, 10 comandos AST, duas cores; C emitido |
| CLI casa com --tokens --ast --so-c | Retorno 0 e arquivo C gravado |
| CLI casa com --executar | Retorno 2 por compilador ausente, sem fingir execução |
| Assistente local | Testes específicos e 400 pedidos aleatórios da suíte passaram |
| Cliente Claude | Testes HTTP simulados passaram; nenhuma chamada com credenciais reais |
| Conversor CLI PPM → PNG | Passou com PPM sintético de 2×1; saída 6×3 por fator 3 |
| Integridade do PNG | Dimensões, CRC dos blocos e pixels descomprimidos conferidos independentemente |
| Janela Studio real | Abriu, processou eventos e fechou |
| Pedido local no Studio | Gerou o quadrado pedido, validou e exibiu C; informou falta de compilador |
| Editor e diagnósticos Studio | Edição/execução de fontes com erros léxico, sintático e semântico; tags de linha conferidas |
| Salvar .td no Studio | Conteúdo salvo conferido |
| Exportar PNG e PPM no Studio | Bytes conferidos com fixture sintética, sem execução C |
| Falha ao exportar em pasta ausente | Diálogo de erro verificado, sem exceção não tratada |
| executar_studio.bat e construir_exe.bat | Executados no cmd no caminho de falha por ausência de py; falha propagada |
| C compilado, PPM real e pixels de ponta a ponta | Não executados: compilador indisponível |
| PyInstaller e executável Windows | Não executados: módulo indisponível |

Os sete testes pulados são: dois de geração C, um de ponta a ponta do
assistente local, três de pipeline e um de GUI completa. A GUI completa requer
opt-in e compilador. O teste parcial da janela descrito acima não substitui
essas verificações.

## Problemas encontrados e correções

1. O lexer deixava escapar ValueError na conversão de literal decimal maior
   que o limite ativo do Python. Agora gera diagnóstico léxico.
2. Preferências JSON podiam ser uma lista, número ou null, causando falha em
   `.get` na GUI. O carregamento só retorna objetos dicionário.
3. Nomes de saída podiam passar na semântica e falhar no Windows, como NUL.ppm
   e nomes com `?` ou `*`. Foram acrescentadas verificações de caracteres de
   controle, caracteres proibidos e nomes reservados comuns.
4. Falhas de inicialização/timeout de processos podiam escapar ao executor.
   Compilação tem timeout de 60 s e retorna falha estruturada; execução
   reporta erro ao iniciar. O timeout existente de execução foi preservado.
5. Leitor PPM aceitava dimensões inválidas ou máximo de canal diferente de 255;
   gerador PNG aceitava fator inválido e raster inconsistente. Agora rejeitam.
6. CLI podia encerrar com traceback em fonte não UTF-8 ou saída não gravável.
   Esses erros recebem mensagem e código 1.
7. A exibição AST usava caracteres de árvore não codificáveis em stdout CP1252
   redirecionado. A marcação foi trocada por ASCII e testada em subprocesso.
8. O runtime C não conferia o retorno da escrita dos pixels nem do fechamento.
   Agora retorna erro nesses casos. **Alteração revisada por leitura; sua
   compilação e exercício no runtime permanecem pendentes de GCC.**
9. O comentário C de origem podia conter quebras de linha. A origem agora é
   achatada no comentário, preservando também o tratamento de `*/` já existente.
10. Salvamento/exportação da GUI podia deixar OSError escapar do callback.
    Agora informa o erro por diálogo. Abertura também trata falha de decodificação.
11. Os `.bat` não preservavam de forma explícita a falha após a pausa.
    Agora encerram com o resultado de execução/empacotamento.
12. O ponto de entrada do autoteste foi preparado para `sys.stdout=None` do
    pacote sem console. O arquivo de resultado continua sendo escrito.
    O comportamento empacotado permanece pendente de PyInstaller.

## Documentação, comentários e estudo

O README contém objetivo, problema, linguagem, arquitetura, pastas, dependências,
Windows, comandos `py`, Studio, imagens, testes, PyInstaller, assistentes,
limitações, documentos e os três integrantes.

O guia aborda os doze tópicos solicitados: fundamentos, arquitetura, léxico,
gramática/parser/AST, semântica, C/runtime, compilação/imagem, Studio, interfaces
reais dos módulos, exemplo completo, perguntas e roteiro de demonstração.
Traz 50 perguntas com respostas, um exemplo 6×4 conferível, exercícios de previsão
e mudança e rodízio de papéis para estudo individual. A imagem do exemplo é
marcada como **previsão**, pois não foi produzida pelo C neste ambiente.

Os comentários/docstrings explicam contratos de entrada/retorno do transpilador,
pipeline e semântica, seleção de produções do parser, conversão extrema de
inteiros, nomes C para cores, índice linear de pixels, dimensões inclusivas,
composição de figuras no assistente, escrita de PPM e fila/thread da GUI.
Não foi feita uma substituição da arquitetura nem comentada cada linha.

Foram retirados emojis desnecessários dos dois botões principais. A documentação
técnica foi alinhada com a AST mutável, a conversão PNG existente, as três
tentativas totais de API e a regra efetiva sobre posição da tela. Afirmações
anteriores de autoria, uso de ferramentas e testes de mutação não comprovados
foram substituídas por registro transparente a confirmar pela equipe.

Não foram atribuídas tarefas históricas aos integrantes nem criada evidência
fictícia de participação. O uso de Codex nesta revisão está declarado em
AUTORIA_E_IA.md. A equipe ainda deve registrar suas próprias verificações.

## Evidências e reprodução

- `testes_revisao.txt`: saída integral da suíte final.
- `validacoes_revisao.txt`: importações, exemplos, janela parcial, conversão e caminhos de erro.
- `rastreamento_estudo/`: tokens, AST, tabela e C gerados do exemplo real.
- `tests/test_regressoes.py`: testes automatizados das correções.
- `tests/verificar_studio_parcial.py`: verificação da janela real sem depender de GCC/API.

Na raiz do projeto, para reproduzir os testes disponíveis:

```powershell
py -m unittest discover -v
py tests/verificar_studio_parcial.py
py ferramentas/rastrear_exemplo.py
```

O teste parcial abre uma janela e usa pastas temporárias/configuração isolada.
Ele simula deliberadamente compilador ausente e usa imagem sintética para testar
exportação. Não é uma demonstração de compilação C.

## Pendências antes da apresentação

1. Instalar/configurar Python com launcher `py` e GCC no computador final.
2. Rodar a suíte e exigir que os testes C deixem de ser pulados.
3. Ativar `TINYDRAW_TESTE_GUI=1` e rodar a GUI completa.
4. Compilar/executar casa, moldura, sobreposição e estudo, conferindo PPM e PNG.
5. Conferir manualmente a imagem, abrir/exportar arquivos e executar o roteiro
   de mudança de ponto e sobreposição sem ler respostas prontas.
6. Executar os `.bat` no caminho de sucesso, instalar PyInstaller e gerar
   `dist/TinyDrawStudio.exe`; testar abertura e `--autoteste` no destino com GCC.
7. Se a API for apresentada, testar uma chamada real autorizada pela equipe
   com seu modelo/chave. O núcleo pode ser demonstrado sem esse recurso.
8. Completar memorial e declaração de IA com fatos verificáveis e realizar
   ensaio individual com troca de papéis.

Essas pendências são materiais para a entrega: a revisão do Python e da
documentação não permite afirmar que toda a cadeia C/executável está validada.

## Arquivos alterados e novos

| Estado | Arquivo |
|---|---|
| Alterado | `construir_exe.bat` |
| Novo | `docs/AUTORIA_E_IA.md` |
| Alterado | `docs/DOCUMENTACAO.md` |
| Novo | `docs/GUIA_DE_ESTUDOS.md` |
| Novo | `docs/rastreamento_estudo/ast.txt` |
| Novo | `docs/rastreamento_estudo/estudo.c` |
| Novo | `docs/rastreamento_estudo/tabela.txt` |
| Novo | `docs/rastreamento_estudo/tokens.txt` |
| Novo | `docs/RELATORIO_REVISAO.md` |
| Novo | `docs/testes_revisao.txt` |
| Novo | `docs/validacoes_revisao.txt` |
| Alterado | `executar_studio.bat` |
| Novo | `exemplos/validos/estudo.td` |
| Novo | `ferramentas/rastrear_exemplo.py` |
| Alterado | `README.md` |
| Alterado | `runtime/tinydraw.c` |
| Alterado | `runtime/tinydraw.h` |
| Novo | `tests/test_regressoes.py` |
| Novo | `tests/verificar_studio_parcial.py` |
| Alterado | `tinydraw/ast_nodes.py` |
| Alterado | `tinydraw/cli.py` |
| Alterado | `tinydraw/codegen.py` |
| Alterado | `tinydraw/compilador.py` |
| Alterado | `tinydraw/config.py` |
| Alterado | `tinydraw/executor.py` |
| Alterado | `tinydraw/gui.py` |
| Alterado | `tinydraw/ia_local.py` |
| Alterado | `tinydraw/imagem.py` |
| Alterado | `tinydraw/lexer.py` |
| Alterado | `tinydraw/parser.py` |
| Alterado | `tinydraw/pipeline.py` |
| Alterado | `tinydraw/semantica.py` |
| Alterado | `tinydraw_studio.py` |
