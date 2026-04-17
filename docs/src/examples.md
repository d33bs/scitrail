# Examples

The notebook below runs the CU Anschutz + Quantum example and renders the
resulting report directly in notebook output as formatted Markdown/HTML.

## Execute Notebook

Use the docs/notebooks dependency groups to execute in a docs-focused env:

```bash
uv run --group docs --group notebooks --frozen jupyter nbconvert \
  --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=1200 \
  docs/src/examples/cu_anschutz_quantum.ipynb
```

## Notebook

```{toctree}
---
maxdepth: 1
---
examples/cu_anschutz_quantum
```
