# Bitácora

[Español](README.md) · [English](README.en.md) · [Português](README.pt-BR.md)

**Um guia conversacional para explorar oportunidades de negócio com um assistente de IA, sem entregar a decisão à IA.**

Bitácora ajuda a transformar uma experiência, uma curiosidade, uma ideia que você viu — ou simplesmente “não sei por onde começar” — em possibilidades que valem ser mais bem compreendidas. Seu objetivo não é prometer um negócio validado: é ajudar você a aprender o que investigar, o que ainda é hipótese e qual pode ser seu próximo experimento.

Ela foi pensada para quem quer empreender, mas ainda não tem uma direção clara, ou quer testar uma que já tem. Você define o ritmo: pode abrir opções, investigar várias, escolher uma, voltar ou pausar.

## Como funciona

1. **Comece de onde está.** Conte uma experiência, uma curiosidade, uma ideia que viu ou diga que ainda não tem tema. O guia apresenta possibilidades e perguntas que podem mudar uma decisão, sem exigir questionário nem uma ideia pronta.
2. **Abra o mapa.** Mantenha separados observações, pistas externas, fatos, hipóteses e dúvidas. Você pode continuar explorando sem se comprometer com uma oportunidade.
3. **Escolha o que contrastar.** Quando quiser, priorize um ou mais candidatos. O guia compara evidências, alternativas, acesso e objeções; uma tendência ou concorrente não é apresentada como validação.
4. **Decida o próximo experimento.** Considerando seus objetivos, tempo e recursos, você recebe uma recomendação fundamentada e sua principal objeção. Só você decide aprofundar, descartar, manter opções abertas ou pausar. Se escolher uma oportunidade, o guia pode sugerir um experimento pequeno; nunca o executa por você.

## Comece em três passos

1. Clone ou baixe este repositório no seu computador.
2. Abra a pasta com um assistente de programação com IA que consiga ler [`AGENTS.md`](AGENTS.md).
3. Inicie uma conversa naturalmente. Por exemplo: *“Quero aprender a empreender, mas não sei por onde começar.”*

Você não precisa instalar um aplicativo nem preencher um formulário. Bitácora é um repositório de instruções para usar com um assistente compatível e funciona na sua cópia local.

## Privacidade e limites

- Trabalhe na sua própria cópia do repositório. O guia não deve salvar nem repetir nomes, contatos, empregador, endereço ou outros identificadores; para detalhes sensíveis, propõe uma versão geral e pede confirmação antes de salvar.
- Sua bitácora não é compartilhada com outra pessoa, a menos que vocês cocriem explicitamente no mesmo repositório. Bitácora não envia mensagens, não publica, não faz compras nem gastos em seu nome.
- Ela separa evidência de hipótese. Uma fonte não lida, um exemplo, uma tendência ou a existência de concorrentes não prova, por si só, demanda ou que uma oportunidade funcionará.
- Os materiais em [`pruebas/`](pruebas/) são exemplos fictícios: verificam o protocolo e não são memórias reais nem evidência de mercado.
- Não substitui pesquisa, validação com pessoas, aconselhamento profissional ou execução. Não cria um plano de negócios completo, não abre uma empresa e não garante resultados.

## Dentro do repositório

| Arquivo ou pasta | Para que serve |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | O protocolo que o assistente segue durante a conversa. |
| [`bitacora/PLANTILLA.md`](bitacora/PLANTILLA.md) | Ponto de partida para sua bitácora pessoal. |
| [`guias/`](guias/) | Guias de contraste e memória, consultados quando necessário. |
| [`pruebas/`](pruebas/) | Exemplos fictícios e verificações do comportamento esperado. |
| [`scripts/`](scripts/) | Utilitários para verificar o protocolo e avaliar conversas. |

## Verificações locais

```text
python scripts/lint_protocolo.py
python -m unittest discover -s pruebas -p test_evaluar.py
python scripts/evaluar_conversaciones.py --help
```

## Licença e contribuições

Bitácora é um ponto de partida aberto para explorar conversas melhores sobre empreendedorismo. Antes de alterar o protocolo, leia [`AGENTS.md`](AGENTS.md), preserve a diferença entre evidência e hipóteses e não transforme uma sugestão em promessa de resultado.
