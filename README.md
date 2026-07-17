# NLCSWebViewer

See `CLAUDE.md` for full project context (what NLCS++ is, repo layout, conventions).
This file covers day-to-day operational steps.

## Running Dekart locally

This dev machine has **no sudo and no Docker**, so Dekart runs via the
[udocker](https://github.com/indigo-dc/udocker) shim instead of `docker run`. Never
substitute plain `docker`/`sudo` commands here.

### Start it

```bash
~/.local/bin/udocker run dekart
```

This is a foreground process — background it (`&`) or run it in a separate terminal.
It serves on `http://localhost:8080`.

### Check it's up

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080
```

### Inspect the container

```bash
~/.local/bin/udocker ps -m -s
```

### Stop it

Killing the wrapper shell/python process that launched `udocker run` does **not**
kill the actual server. Kill the `proot` process directly (the one running
`/dekart/server`):

```bash
ps aux | grep '/dekart/server'
kill <proot_pid> <dekart_server_pid>
```

### Restart

Stop, then start again. State (reports, datasets, uploaded files) persists across
restarts inside the container rootfs under `~/.udocker`, so nothing is lost.

### Multi-user note

If a teammate is also running their own instance on this machine (e.g. on a
different `DEKART_PORT`), `ps`/`grep` for `/dekart/server` will show both. Make sure
you kill the PID under your own user, not theirs.

### CLI

The `dekart` CLI (installed in `~/.local/venvs/dekart`, on `PATH`) drives report/
dataset/file creation and snapshots against the running server — see the **geosql**
skill and `CLAUDE.md`'s "Dekart CLI pitfalls" section for the workflows and gotchas.
