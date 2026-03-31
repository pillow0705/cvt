# Agent Installation Guide

Follow these two steps in order. Do not read other files in this repository.

## Step 1: Install the software

```bash
pip install "cvt-tool[full]"
```

Verify installation:

```bash
cvt --version
```

## Step 2: Install the skill

```bash
mkdir -p ~/.claude/skills/cvt
cp SKILL.md ~/.claude/skills/cvt/SKILL.md
```

Done. The `cvt` command is now available and the skill is registered.
