# ngdj command reference

`ngdj` is the short name for the `angular-django2` Angular CLI schematics
collection. This reference documents its published command surface only.

## Install and discover

From an Angular workspace, install and register the collection:

```text
npm install angular-django2
ng add angular-django2
```

Run schematic-specific help with:

```text
ng generate angular-django2:<schematic> --help
```

## djng integration legend

Each command table below adds three djng-side indicators (source of truth:
`TODO.md` §1.1):

- **djng wrapper** — the djng command that resolves this schematic, or `—` when
  no wrapper exists yet.
- **Integration** — `Complete` (wrapper resolves and is covered by tests),
  `Wrapper; build_app pending` (standalone wrapper exists, change-driven
  `build_app` execution still blocked on the unimplemented engine), or
  `Pending` (no djng wrapper yet).
- **djng docs** — where the command is documented on the djng side beyond this
  reference (`—` / `Reference only` means this file is the only djng coverage).

## Collection registration

| Command | Purpose | Options | djng wrapper | Integration | djng docs |
| --- | --- | --- | --- | --- | --- |
| `ng add angular-django2` | Register `angular-django2` as a schematic collection in `angular.json`. | None. | `ng_add` (also folded into `ng_workspace`) | Complete | `docs/commands.md`, `README.md` |

When configuring the collection manually, place `angular-django2` before the
default Angular collection in `cli.schematicCollections`.

## Application and workspace schematics

| Command | Purpose | Documented options | djng wrapper | Integration | djng docs |
| --- | --- | --- | --- | --- | --- |
| `ng generate angular-django2:workspace-setup <name>` | Initialize workspace-level bootstrap and validation files for an empty Angular workspace. | `--project` is optional. The advanced `files` hooks are programmatic rather than command-line options. | `ng_workspace`, `ng_workspace_modify` | Complete | `docs/commands.md`, `README.md`, SKILL 01 |
| `ng generate angular-django2:application <name>` | Generate an Angular application using package defaults. | `--routing=true`, `--standalone=true`, `--ssr=false`, `--zoneless=true`, `--style=scss`. | — | Pending | Reference only |
| `ng generate angular-django2:material-app <name>` | Generate a Django-friendly Angular application with Material UI and a sidenav layout. | `--theme=indigo-pink`, `--typography=true`, `--animations=true`, `--routing=true`, `--standalone=true`, `--ssr=false`, `--zoneless=true`, `--defaults=true`, `--style=scss`, `--prefix=app`. | `ng_gen_app` | Complete | `docs/commands.md`, `README.md`, SKILL 02 |
| `ng generate angular-django2:material-setup --project=<name>` | Configure Angular Material in an existing project. | `--theme`, `--typography`, `--animations`. | — | Pending | Reference only |
| `ng generate angular-django2:project-structure --project=<name>` | Create the standard `core/`, `shared/`, and `features/` structure. | `--prefix=app`. | — (emitted within `material-app`) | Via `material-app`; contract-tested | SKILL 02 |
| `ng generate angular-django2:app-shell --project=<name>` | Generate or update the application shell. | `--project`. | — | Pending | SKILL 02, SKILL 11 |

For an empty workspace, the documented flow is:

```text
ng generate angular-django2:workspace-setup my-app
ng generate angular-django2:material-app my-app --ssr=false --zoneless=true --defaults
npm install
ng build my-app
ng serve my-app
```

## Component and utility schematics

| Command | Purpose | Documented options | djng wrapper | Integration | djng docs |
| --- | --- | --- | --- | --- | --- |
| `ng generate angular-django2:component <name>` | Generate a standalone, `OnPush` component with embedding hooks. | Project-relative `--path`, `--project`, `--standalone=true`, `--changeDetection=OnPush`. | — | Pending | `docs/workflow.md` §6, `README.md`, SKILL 07 |
| `ng generate angular-django2:embed-component --component=<path> --parent=<path>` | Embed a child component into a parent. | File mode uses `--component` and `--parent`. Package mode adds `--from` and supports `--selector`, `--inputs`, and `--outputs`. | — | Pending | `docs/workflow.md` §6, `README.md`, SKILL 07 |
| `ng generate angular-django2:complex-component <name> --path=<path> --features=<features>` | Generate, update, or remove an advanced standalone `OnPush` Angular Material component. | The positional name, `--path`, and comma-separated `--features` are required; use `--project` where needed. Features: `mixins`, `nested`, `projection`, `cdk-overlay`. Use `--mode=modify` for additions; deletion requires `--mode=delete --confirm=true`. | `ng_complex_component` | Complete | `docs/commands.md`, SKILL 08 |
| `ng generate angular-django2:service <name>` | Generate a service. | Project-relative `--path`, `--project`. | — | Pending | Reference only |
| `ng generate angular-django2:class <name>` | Generate a class. | Project-relative `--path`, `--project`. | — | Pending | Reference only |

`embed-component` is idempotent: it wires the child element, imports, imports
array entry, and output-handler stubs into the parent. `complex-component`
requires `@angular/material` and `@angular/cdk` to be installed.

## OpenAPI schematics

| Command | Purpose | Documented options | djng wrapper | Integration | djng docs |
| --- | --- | --- | --- | --- | --- |
| `ng generate angular-django2:openapi-setup --openapi_spec_file=openapi.json` | Bootstrap `ng-openapi-gen` and generate Django integration helpers. | `--openapi_spec_file=openapi.json`, `--outputPath=src/app/api`, `--helpersPath=src/app/api-integration`, `--skipHelpers=false`, `--skipTests=false`. | `ng_openapi_setup` | Wrapper; build_app pending | SKILL 03, `docs/commands.md` |
| `ng generate angular-django2:data-service <name>` | Generate a typed `*DataService` wrapper around a generated OpenAPI service. | `--project`, `--path`, `--apiService` (inferred from name), `--apiPath=../api/services`, `--flat=false`, `--skipTests=false`. | `ng_data_service` | Wrapper; build_app pending | SKILL 04, `docs/commands.md` |

`openapi-setup` writes `ng-openapi-gen.json`, adds `ng-openapi-gen` to
development dependencies, and adds the `generate:api` npm script. Generate the
OpenAPI client before creating a data-service wrapper:

```text
ng generate angular-django2:openapi-setup --openapi_spec_file=openapi.json
npm install
npm run generate:api
ng generate angular-django2:data-service users
```

## Sources

- [ngdj CLI reference](https://angular-django2.readthedocs.io/en/latest/cli/)
- [ngdj README](https://github.com/shlomoa/angular-django2/blob/main/README.md)
