## ADDED Requirements

### Requirement: removeBillingModule uses dash-delimited block markers

`removeBillingModule()` SHALL identify billing-related blocks in settings files and configuration using dash-delimited comment markers (`# --- BILLING MODULE ---` / `# --- END BILLING MODULE ---`), not line-count heuristics or content-based scanning.

**Rationale:** Line-count heuristics break when unrelated lines are added above or below the billing block. Content scanning requires knowing every billing-specific string. Explicit block markers are robust to surrounding changes and unambiguous regardless of file content between them.

_(Decision: Phase 12-02)_

#### Scenario: Billing settings block removed correctly

- **WHEN** `removeBillingModule()` processes `config/settings/base.py`
- **THEN** all lines between `# --- BILLING MODULE ---` and `# --- END BILLING MODULE ---` (inclusive) are removed

#### Scenario: Non-billing settings are preserved

- **WHEN** `removeBillingModule()` processes any settings file
- **THEN** lines outside billing block markers are unchanged

---

### Requirement: --without billing flag removes billing module from scaffolded projects

The `create-foundation-app` CLI SHALL support a `--without billing` flag (and its hyphenated form `--without-billing`). When provided, the billing module SHALL be removed from the generated project after scaffolding.

**Rationale:** The interactive prompt already offers a billing opt-out via checkbox. The `--without billing` flag enables non-interactive (CI/scripted) use of the scaffolder without requiring TTY input. Both space-separated and hyphenated forms SHALL be supported for UX consistency.

_(Decision: Phase 12-02)_

#### Scenario: Flag removes billing in non-interactive mode

- **WHEN** `create-foundation-app --without billing` is run
- **THEN** the generated project has no billing Django app, no billing frontend pages, no billing environment variables, and no billing entry in `INSTALLED_APPS`

#### Scenario: Hyphenated flag form is also accepted

- **WHEN** `create-foundation-app --without-billing` is run
- **THEN** the result is identical to `--without billing`

#### Scenario: Interactive prompt without flag preserves billing

- **WHEN** the user selects "include billing" in the interactive prompt
- **THEN** the billing module is present in the generated project

---

### Requirement: CLI source uses fs-extra default import pattern for Node.js v24 compatibility

All CLI source files that import from `fs-extra` SHALL use the default import + destructuring pattern:

```typescript
import fse from "fs-extra";
const { readFile, writeFile, remove } = fse;
```

Named imports (`import { readFile } from 'fs-extra'`) SHALL NOT be used.

**Rationale:** Node.js v24 enforces stricter ESM/CJS interoperability. `fs-extra` is a CommonJS module that does not declare named exports in its ESM wrapper. Node.js v24 rejects named imports from such modules with `SyntaxError: Named export not found`. The default import + destructuring pattern works in both Node.js v20 and v24 because it accesses the module's default export object, which carries all methods.

_(Decision: Phase 12)_

#### Scenario: CLI builds without error on Node.js v24

- **WHEN** the CLI package is built with `tsup` targeting Node.js v24
- **THEN** no `SyntaxError: Named export not found` errors occur for `fs-extra` imports

#### Scenario: fs-extra methods available after destructuring

- **WHEN** CLI code destructures `readFile`, `writeFile`, `remove` from the default import
- **THEN** all methods work identically to the named import versions

---

### Requirement: CLI invoked via inline module script in integration tests

Integration tests that exercise the full CLI SHOULD invoke it via `node --input-type=module` with an inline `import(...)` script rather than calling `dist/index.js` directly.

**Rationale:** `dist/index.js` is the interactive entrypoint and requires a TTY for prompts. Direct invocation blocks or crashes in non-interactive test environments. An inline module script can import and call specific compiled modules (e.g., `dist/remove.js`) directly, bypassing interactive prompts while still exercising the compiled TypeScript output.

_(Decision: Phase 12)_

#### Scenario: Integration test invokes billing removal non-interactively

- **WHEN** a pytest test runs `node --input-type=module -e "import('./dist/remove.js').then(m => m.removeBillingModule(path))"`
- **THEN** the billing module is removed from the target path without requiring TTY input
