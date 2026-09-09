# Bitácora

[Español](README.md) · [English](README.en.md) · [Português](README.pt-BR.md)

**A conversational guide for exploring business opportunities with an AI assistant, without handing the decision to AI.**

Bitácora helps turn an experience, a curiosity, an outside idea—or simply “I do not know where to start”—into possibilities worth understanding better. Its goal is not to promise a validated business: it helps you learn what to investigate, what remains a hypothesis, and what your next experiment could be.

It is for people who want to start a business but do not yet have a clear direction, or who want to test one they already have. You set the pace: open options, investigate several, choose one, go back, or pause.

## How it works

1. **Start where you are.** Share an experience, a curiosity, an idea you saw, or say you have no topic yet. The guide offers possibilities and questions that could change a decision; it does not require a questionnaire or a fully formed idea.
2. **Open the map.** Keep observations, external leads, facts, hypotheses, and unknowns separate. You can keep exploring without committing to an opportunity.
3. **Choose what to test.** Whenever you are ready, prioritize one or several candidates. The guide compares evidence, alternatives, access, and objections; a trend or competitor is not presented as validation.
4. **Decide the next experiment.** With your goals, time, and resources in view, you receive a reasoned recommendation and its main objection. Only you decide whether to go deeper, discard it, keep options open, or pause. If you choose an opportunity, the guide can suggest a small experiment; it never runs it for you.

## Start in three steps

1. Clone or download this repository to your computer.
2. Open the folder with an AI coding assistant that can read [`AGENTS.md`](AGENTS.md).
3. Start a conversation naturally. For example: *“I want to learn entrepreneurship, but I do not know where to begin.”*

You do not need to install an application or complete a form. Bitácora is a repository of instructions for a compatible assistant and works from your local copy.

## Privacy and boundaries

- Work in your own copy of the repository. The guide must not save or repeat names, contact details, employer, address, or other identifiers; for sensitive details, it proposes a general version and asks for confirmation before saving it.
- Your journal is not shared with another person unless you explicitly co-create in the same repository. Bitácora does not send messages, publish, make purchases, or spend money on your behalf.
- It separates evidence from hypotheses. An unread source, an example, a trend, or the existence of competitors does not by itself prove demand or that an opportunity will work.
- The material in [`pruebas/`](pruebas/) consists of fictional examples: it checks the protocol and is neither real memory nor market evidence.
- It does not replace research, validation with people, professional advice, or execution. It does not produce a complete business plan, incorporate a company, or guarantee outcomes.

## Inside the repository

| File or folder | Purpose |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | The protocol the assistant follows during the conversation. |
| [`bitacora/PLANTILLA.md`](bitacora/PLANTILLA.md) | Starting point for your personal journal. |
| [`guias/`](guias/) | Contrast and memory guides, read when they are needed. |
| [`pruebas/`](pruebas/) | Fictional examples and checks for the expected behavior. |
| [`scripts/`](scripts/) | Utilities to check the protocol and evaluate conversations. |

## Local checks

```text
python scripts/lint_protocolo.py
python -m unittest discover -s pruebas -p test_evaluar.py
python scripts/evaluar_conversaciones.py --help
```

## License and contributions

Bitácora is an open starting point for exploring better entrepreneurship conversations. Before changing the protocol, read [`AGENTS.md`](AGENTS.md), preserve the distinction between evidence and hypotheses, and do not turn a suggestion into a promise of results.
