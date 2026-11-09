# Demo captures

The registered `demo-capture` targets: the pages the `demo-capture` Hook
([HOOK_CONTRACTS.md](HOOK_CONTRACTS.md)) captures with the `demo_capture` Tool
([TOOL_CONTRACTS.md](TOOL_CONTRACTS.md)), and the exact steps that reproduce each capture
locally. The table below is the registry: a page is a target when it has a row here.

Every row must fill all five columns; the Hook fails on an empty cell. The URL is the
page the Tool captures; the application must already be running there (the end-to-end
flow, `tests/e2e/run_e2e.py` stage 6c, boots it). Screenshots are written to
`build/demo/` and uploaded as CI artifacts; they are never compared pixel by pixel.

| Target | URL | Server command | Fixture setup | Actions |
|---|---|---|---|---|
| home | http://127.0.0.1:8000/ | `python manage.py runserver 127.0.0.1:8000 --noreload` in the end-to-end tutorial project, after `DJNG_E2E=1 python -m tests.e2e.run_e2e` built it | `python manage.py loaddata tests/e2e/fixtures/seed.json` | Open the URL. |
| customers | http://127.0.0.1:8000/customers | the same | the same | Open the URL; the first page of ten seeded customers is listed. |
| products | http://127.0.0.1:8000/products | the same | the same | Open the URL. |
