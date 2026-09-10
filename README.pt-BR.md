# Bitácora

[Español](README.md) · [English](README.en.md) · [Português](README.pt-BR.md)

**Um guia conversacional para explorar oportunidades de negócio com um assistente de IA, sem entregar a decisão à IA.**

Bitácora ajuda a transformar uma experiência, uma curiosidade, uma ideia que você viu — ou simplesmente “não sei por onde começar” — em possibilidades que valem ser mais bem compreendidas. Seu objetivo não é prometer um negócio validado: é ajudar você a aprender o que investigar, o que ainda é hipótese e qual pode ser seu próximo experimento.

Ela foi pensada para quem quer empreender, mas ainda não tem uma direção clara, ou quer testar uma que já tem. Você define o ritmo: pode abrir opções, investigar várias, escolher uma, voltar ou pausar.

Ao pausar, seu arquivo pessoal conserva um resumo de opções, decisões e incertezas para retomar em uma nova conversa.

## Como funciona

1. **Comece de onde está.** Conte uma experiência, uma curiosidade, uma ideia que viu ou diga que ainda não tem tema. O guia apresenta possibilidades e perguntas que podem mudar uma decisão, sem exigir questionário nem uma ideia pronta.
2. **Abra o mapa.** Mantenha separados observações, pistas externas, fatos, hipóteses e dúvidas. Você pode continuar explorando sem se comprometer com uma oportunidade.
3. **Escolha o que contrastar.** Quando quiser, priorize um ou mais candidatos. O guia compara evidências, alternativas, acesso e objeções; uma tendência ou concorrente não é apresentada como validação.
4. **Decida o próximo experimento.** Considerando seus objetivos, tempo e recursos, você recebe uma recomendação fundamentada e sua principal objeção. Só você decide aprofundar, descartar, manter opções abertas ou pausar. Se escolher uma oportunidade, o guia pode sugerir um experimento pequeno; nunca o executa por você.

## Uma nota sobre o idioma

`AGENTS.md` e a pasta `guias/` estão escritos em espanhol — é lá que vive o protocolo em si. Você não precisa lê-los nem traduzi-los: o guia vai conversar, recomendar e escrever sua bitácora no idioma que você usar, sem supor seu país ou mercado-alvo a partir disso.

## Comece em três passos

Você precisa de um assistente de programação com IA capaz de ler `AGENTS.md` — por exemplo, [Claude Code](https://claude.com/claude-code) ou [Cursor](https://cursor.com); a maioria desses assistentes exige uma assinatura paga. Python **não** é necessário para usar Bitácora: só é preciso para rodar as verificações locais do protocolo (veja abaixo).

1. Clone ou baixe este repositório no seu computador.
2. Com Claude Code instalado e autenticado, abra um terminal na pasta baixada e execute `claude`. Permita a leitura das instruções do projeto: `CLAUDE.md` remete a [`AGENTS.md`](AGENTS.md).
3. Inicie uma conversa naturalmente. Por exemplo: *“Quero aprender a empreender, mas não sei por onde começar.”*

Você não precisa instalar um aplicativo nem preencher um formulário. Bitácora é um repositório de instruções para usar com um assistente compatível e funciona na sua cópia local.

São necessárias permissões de leitura do protocolo e escrita para salvar `bitacora/ACTUAL.md`. Fontes externas verificadas exigem navegação e acesso ao conteúdo; sem isso, o guia deve explicar a limitação. Ao pausar, fica um resumo de opções, decisões e incertezas. Abra uma nova conversa na mesma pasta e diga “Vamos retomar”. A PLANTILLA.md permanece intacta. Para memórias anteriores, informe o caminho quando solicitado.

São instruções de conduta, não isolamento técnico: o cumprimento depende do assistente e das permissões. `.gitignore` não impede leituras pelo assistente nem apaga histórico, memória ou cópias do provedor. Cursor tem uma regra de entrada, mas leitura seletiva e retomada ainda não foram testadas; outras plataformas também não estão verificadas.

## Privacidade e limites

- Sua conversa viaja até o provedor de IA do assistente que você usa (por exemplo, a Anthropic, se você usa o Claude Code); confira a política de privacidade dele antes de compartilhar algo sensível.
- Trabalhe na sua própria cópia do repositório. O guia não deve salvar nem repetir nomes, contatos, empregador, endereço ou outros identificadores; para detalhes sensíveis, propõe uma versão geral e pede confirmação antes de salvar.
- Sua bitácora pessoal vive em `bitacora/`, e o `.gitignore` a mantém fora do git: ela nunca é enviada sozinha quando você faz um commit. O protocolo proíbe compartilhá-la com outra pessoa, a menos que vocês cocriem explicitamente no mesmo repositório. O protocolo proíbe executar contatos, publicações, compras ou gastos em seu nome.
- Ela separa evidência de hipótese. Uma fonte não lida, um exemplo, uma tendência ou a existência de concorrentes não prova, por si só, demanda ou que uma oportunidade funcionará.
- [`pruebas/`](pruebas/) contém ilustrações fictícias, testes e relatórios de avaliação identificados separadamente. Os exemplos não são memórias reais nem evidência de mercado. Você pode ler [um exemplo completo de conversa](pruebas/conversacion-01.md) para ver como funciona na prática.
- Não substitui pesquisa, validação com pessoas, aconselhamento profissional ou execução. Não cria um plano de negócios completo, não abre uma empresa e não garante resultados.

## Dentro do repositório

| Arquivo ou pasta | Para que serve |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | O protocolo que o assistente segue durante a conversa. |
| [`bitacora/PLANTILLA.md`](bitacora/PLANTILLA.md) | Ponto de partida para sua bitácora pessoal. |
| [`guias/`](guias/) | Guias de contraste e memória, consultados quando necessário. |
| [`pruebas/`](pruebas/) | Exemplos fictícios e verificações do comportamento esperado. |
| [`scripts/`](scripts/) | Utilitários para verificar o protocolo e avaliar conversas. |
| [`LICENSE`](LICENSE) | A licença MIT sob a qual este repositório é publicado. |

## Verificações locais

A [avaliação de 2026-09-09](pruebas/evaluacion-20260909.md) distingue testes reais e limitações observadas: o contraste comercial continua parcial. Veja [CONTRIBUTING.md](CONTRIBUTING.md) para reproduzir as verificações.

```text
python3 scripts/lint_protocolo.py
python3 -m unittest discover -s pruebas
python3 scripts/evaluar_conversaciones.py --help
```

No Windows, onde `python3` geralmente não existe, use `python` no lugar.

## Licença e contribuições

Bitácora é publicado sob a licença [MIT](LICENSE): você pode usá-lo, copiá-lo e modificá-lo livremente, inclusive para fins comerciais, desde que credite a licença original. Antes de alterar o protocolo, leia [`AGENTS.md`](AGENTS.md), preserve a diferença entre evidência e hipóteses e não transforme uma sugestão em promessa de resultado.
