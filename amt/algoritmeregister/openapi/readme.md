Clients are generated using openapi-generator.

Run commands from root, to generate the correct structure:

```bash
openapi-generator generate -c amt/algoritmeregister/openapi/v1_0/specs/config.json
```

The config file specifies:

- Generator: `python-pydantic-v1` (uses Pydantic models, compatible with FastAPI)
- Output directory: `amt/algoritmeregister/openapi/v1_0/client` (keeps generated files isolated)
- Package name: `openapi_client`
- Only generates: APIs, models, and supporting files
- Skips: documentation, tests, build files, and CI configs (via `.openapi-generator-ignore`)
- Post-processing: All generated files are automatically formatted with `ruff check --fix`
