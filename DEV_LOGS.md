# Dev Logs: turbo dev vs separate outputs

This repo defaults to a single multiplexed console when you run `pnpm dev`.
Turborepo prefixes each app's output (web, mobile, api) into one stream.

## Option 1: Single combined console (default)

Use this when you want one terminal and prefixed output.

```bash
pnpm dev
```

You will see lines like:

```
@repo/api:dev: ...
@repo/web:dev: ...
@repo/mobile:dev: ...
```

## Option 2: Separate terminals per app

Use this when you want each app in its own terminal.

```bash
pnpm --filter api dev
pnpm --filter web dev
pnpm --filter mobile dev
```

Each terminal becomes the log for that app only.

## Option 3: Separate log files with tee

Use this when you want files for later reference.

```bash
pnpm --filter api dev | tee /tmp/api-dev.log
pnpm --filter web dev | tee /tmp/web-dev.log
pnpm --filter mobile dev | tee /tmp/mobile-dev.log
```

You can tail a file later with:

```bash
tail -f /tmp/api-dev.log
```

## Notes

- `pnpm dev` does not create log files by default.
- If a dev server prompts for a different port, run it in an interactive terminal
  or start that app separately.
