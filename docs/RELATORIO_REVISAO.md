# Revisão atual — remoção da integração online

Data: 02/11/2026. Alterações aplicadas diretamente em
`C:/Users/martt/tranqueiras/TinyDraw_revisado/tinydraw_projeto`.

## Conferência feita antes de remover

Foram lidos os PDFs fornecidos: `08 DAC 681 EC 26B.docx.pdf` e
`propostas-dac-minilinguagens.pdf`. Nenhum deles menciona literalmente Claude,
Anthropic ou API. A proposta 8 exige a DSL de desenhos, transpilação Python/C,
execução e PPM; não exige um serviço externo de geração.

O edital permite IA generativa como ferramenta de apoio ao desenvolvimento e
exige declarar ferramentas, finalidades e verificações da equipe. Essa regra
não exige que o aplicativo tenha IA. A declaração histórica de apoio ao
desenvolvimento permanece em AUTORIA_E_IA.md.

O ZIP original fornecido pelo usuário já continha `tinydraw/ia_claude.py`,
`tests/test_ia_claude.py`, campos de chave/modelo na interface e instruções no
README. Portanto a integração já existia antes da revisão. O Git local contém
somente o commit b8c03f3 da versão revisada como referência anterior disponível;
não é possível afirmar o que havia em versões anteriores ao ZIP não fornecidas.

Não foram encontrados outros PDFs dentro da pasta atual do projeto.

## O que mudou

- Excluído o cliente externo e seus testes exclusivos.
- Retirados seletor de modo, modelo, chave, opção de lembrar e continuação online.
- Retiradas leitura de variável de chave e referências a ela no diagnóstico.
- Excluído o módulo de preferências usado pelo recurso removido. A aplicação
  não lê nem grava mais essas preferências. Arquivo antigo no perfil do usuário
  não foi acessado nem apagado.
- `ia_local.py` foi renomeado para `assistente_local.py`, com imports e testes
  atualizados para deixar claro que se trata de regras locais.
- A fachada agora usa `gerar(pedido, progresso=...)`, sem parâmetros de serviço.
- README, documentação técnica e guia foram atualizados para a versão local.
- Foram mantidos o compilador, runtime C, editor, assistente por regras,
  pré-visualização, diagnósticos e exportação de imagens.

A documentação de autoria não foi usada para afirmar que não houve apoio de IA.
Retirar uma funcionalidade do produto não muda a história do desenvolvimento.

## Verificações desta alteração

Suíte atual: **78 testes descobertos, 71 aprovados, 7 pulados**, sem falhas.
Os testes do serviço removido deixaram de fazer parte da suíte; a redução da
contagem não significa que os testes antigos ainda sejam aplicáveis.
Há novos testes para pedido vazio, geração local sem rede e ausência do módulo
removido. A suíte cobre os 400 pedidos aleatórios do assistente local.

O teste separado da janela real passou: abertura, geração local, edição,
exibição do C, três fases de diagnóstico, gravação .td, exportação PNG/PPM com
imagem sintética e tratamento de falha ao exportar. Também confere que os
campos de modo, chave e modelo não existem.

Os sete testes pulados continuam dependendo do compilador C ou da ativação do
teste completo de interface. A compilação C, imagem gerada pelo executável e
pacote PyInstaller não foram validados nesta alteração.

Evidências: `testes_revisao.txt` e `validacoes_revisao.txt`.

```powershell
py -m unittest discover -v
py tests/verificar_studio_parcial.py
py tinydraw_studio.py
```

## Preparação da entrega

O guia mantém suas doze partes, perguntas explicadas e roteiro de demonstração,
agora sobre o assistente local. O memorial de participação e declaração de
apoio no desenvolvimento precisam ser conferidos pessoalmente pela equipe.
As pendências do núcleo continuam sendo executar GCC, conferir os pixels reais,
testar a interface completa e preparar a defesa oral.

Um backup anterior à remoção foi guardado na área de trabalho do agente, fora
do projeto. O ZIP original e os PDFs em Downloads não foram modificados.
Não foi feito commit nem envio remoto desta alteração.
