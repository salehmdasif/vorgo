# Contributing to Vorgo

Vorgo is MIT licensed and open to contributions.

## Getting Started

```bash
git clone https://github.com/ravelweb/vorgo.git
cd vorgo
pip install -r requirements.txt
cp .env.example .env
make generate-keys
make docker-up
make migrate
make run
```

## Development Workflow

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Make changes
4. Run tests: `make test`
5. Run lint: `make lint`
6. Submit a Pull Request to `develop` branch

## Commit Convention

```
feat: add 2FA support
fix: refresh token rotation bug
docs: update README
chore: bump dependencies
```

## Questions

Open a GitHub Discussion or Issue.
