# Prompts

This document explains how prompts are managed for API-assisted annotation and why we keep them as first-class artifacts.

## Why prompts live in the repo
- prompts are part of the dataset generation pipeline
- changing a prompt changes labels, which changes evaluation and the product behavior
- prompts must be versioned and reviewable like code
