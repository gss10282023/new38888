# Contributing

Thanks for your interest in contributing to **BIOTech Futures Hub**!

## Ways to contribute
- Report bugs and request features via GitHub Issues
- Improve documentation (`README.md`, `docs/`)
- Fix bugs / add features via Pull Requests

## Development setup

### Prerequisites
- Python 3.11+
- Node.js 20.19+ (or 22.12+)

### Quick start (recommended)
```bash
./start_docker.sh
```

### Manual setup
Backend:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Frontend:
```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

## Running tests

All tests:
```bash
./tests/run-all-tests.sh
```

Backend only:
```bash
cd backend
python manage.py test tests.backend tests.api tests.integration --verbosity 2
```

Frontend only:
```bash
cd frontend
npm run test
```

## Linting / formatting

Frontend:
```bash
cd frontend
npm run lint:ci
npm run format
```

## Pull Request guidelines
- Keep PRs small and focused; link issues when possible.
- Add/adjust tests for behavior changes.
- Ensure `CI` is green before requesting review.
- Update docs for user-facing changes.

## Security issues
Please follow `SECURITY.md` and avoid filing public issues for vulnerabilities.

