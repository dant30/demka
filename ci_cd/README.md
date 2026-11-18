# CI/CD

GitHub Actions only discovers workflows under `.github/workflows/`, so the
project's continuous-integration workflow lives at
`.github/workflows/ci.yml`. It checks the Vite frontend and runs the Django
test suite against a temporary PostgreSQL service.

Deployment configuration for Render is maintained in the repository-root
`render.yaml` file. Runtime credentials belong in the hosting provider's secret
store and must not be committed.