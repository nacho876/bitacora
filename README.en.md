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

## A note on language

`AGENTS.md` and the `guias/` folder are written in Spanish — that is where the protocol itself lives. You do not need to read or translate them: the guide will still hold the conversation, recommend, and write your journal in whatever language you use, without assuming your country or target market from it.

## Start in three steps

You need an AI coding assistant able to read `AGENTS.md` — for example, [Claude Code](https://claude.com/claude-code) or [Cursor](https://cursor.com); most of these assistants require a paid subscription. Python is **not** required to use Bitácora: you only need it to run the protocol's local checks (see below).

1. Clone or download this repository to your computer.
2. Open the folder with an AI coding assistant that can read [`AGENTS.md`](AGENTS.md).
3. Start a conversation naturally. For example: *“I want to learn entrepreneurship, but I do not know where to begin.”*

You do not need to install an application or complete a form. Bitácora is a repository of instructions for a compatible assistant and works from your local copy.

## Privacy and boundaries

- Your conversation travels to the AI provider behind the assistant you use (for example, Anthropic if you use Claude Code); check its privacy policy before sharing anything sensitive.
- Work in your own copy of the repository. The guide must not save or repeat names, contact details, employer, address, or other identifiers; for sensitive details, it proposes a general version and asks for confirmation before saving it.
- Your personal journal lives in `bitacora/`, and `.gitignore` keeps it out of git: it is never uploaded on its own when you commit. It is also not shared with another person unless you explicitly co-create in the same repository. Bitácora does not send messages, publish, make purchases, or spend money on your behalf.
- It separates evidence from hypotheses. An unread source, an example, a trend, or the existence of competitors does not by itself prove demand or that an opportunity will work.
- The material in [`pruebas/`](pruebas/) consists of fictional examples: it checks the protocol and is neither real memory nor market evidence. You can read [a full example conversation](pruebas/conversacion-01.md) to see it in practice.
- It does not replace research, validation with people, professional advice, or execution. It does not produce a complete business plan, incorporate a company, or guarantee outcomes.

## Inside the repository

| File or folder | Purpose |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | The protocol the assistant follows during the conversation. |
| [`bitacora/PLANTILLA.md`](bitacora/PLANTILLA.md) | Starting point for your personal journal. |
| [`guias/`](guias/) | Contrast and memory guides, read when they are needed. |
| [`pruebas/`](pruebas/) | Fictional examples and checks for the expected behavior. |
| [`scripts/`](scripts/) | Utilities to check the protocol and evaluate conversations. |
| [`LICENSE`](LICENSE) | The MIT license this repository is published under. |

## Local checks

```text
python3 scripts/lint_protocolo.py
python3 -m unittest discover -s pruebas
python3 scripts/evaluar_conversaciones.py --help
```

On Windows, where `python3` usually is not available, use `python` instead.

## License and contributions

Bitácora is published under the [MIT](LICENSE) license: you can use, copy, and modify it freely, even commercially, as long as you credit the original license. Before changing the protocol, read [`AGENTS.md`](AGENTS.md), preserve the distinction between evidence and hypotheses, and do not turn a suggestion into a promise of results.
