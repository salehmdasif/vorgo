---
title: Getting Started with Vorgo
description: Learn how to set up and customize your Vorgo SaaS.
date: 2026-06-13
---

# Getting Started with Vorgo

Welcome to **Vorgo**, a production-ready, fullstack FastAPI SaaS boilerplate.

## Prerequisites

Ensure you have the following installed on your local machine:
- Python 3.12+
- Docker and Docker Compose
- Redis (optional for native local execution)

## Quick Start

1. Clone the repository and navigate to the directory:
   ```bash
   git clone https://github.com/ravelweb/vorgo.git
   cd vorgo
   ```

2. Install the python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Setup environment configuration:
   ```bash
   cp .env.example .env
   ```

4. Run key generation to generate ED25519 asymmetric token keys:
   ```bash
   make generate-keys
   ```

5. Run database migrations:
   ```bash
   make migrate
   ```

6. Start the development server:
   ```bash
   make run
   ```

Open `http://localhost:8000/dashboard` in your browser. Happy building!
