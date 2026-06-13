---
title: Welcome to the Vorgo SaaS Blog
description: Introducing Vorgo, the Python-only fullstack FastAPI SaaS boilerplate.
date: 2026-06-13
author: Asif
---

# Welcome to Vorgo SaaS!

We are incredibly excited to introduce **Vorgo**, an open-source, production-ready, React-free SaaS boilerplate built on top of **FastAPI**.

## Why We Built Vorgo

Most modern SaaS boilerplates are JavaScript-heavy, forcing developers to deal with React, Next.js, and complicated frontend build pipelines. 

For Python developers, this is often overkill. We wanted to build something that feels **native, fast, and simple**:
- **Python-Only Stack:** Served using standard Jinja2 templates and enhanced with **HTMX** for smooth SPA-like interactivity.
- **Asymmetric Security:** Standard JWT implementations use symmetric keys (HS256). Vorgo uses **ED25519** asymmetric cryptography (via `PyJWT` + `cryptography`), making it microservice-friendly and extremely secure.
- **Robust Multi-Tenancy:** Scoped database routing out of the box.

We hope Vorgo saves you weeks of bootstrapping and lets you focus on building your actual product.

Stay tuned for more updates!
