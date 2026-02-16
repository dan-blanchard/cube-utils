# Unseeded Packs for All Modes — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `--unseeded` work in template mode by generating random card packs and categorizing them into proportional templates, matching the existing grid mode pattern.

**Architecture:** Extract a `packs_to_templates` helper from `generate_grid_templates` that converts card packs into `PackTemplate`s by counting categories. Use this in both grid mode (refactor) and the new unseeded template mode path in the CLI.

**Tech Stack:** Python, Click CLI, pytest

---

### Task 1: Extract `packs_to_templates` helper in `packs.py`

**Files:**
- Modify: `src/cube_utils/packs.py:210-219` (grid template loop)
- Test: `tests/test_packs.py` (existing grid tests verify no regression)

**Step 1: Write the failing test**

Add to `tests/test_packs.py`:

```python
from cube_utils.packs import packs_to_templates

class TestPacksToTemplates:
    """Tests for packs_to_templates helper."""

    def test_converts_packs_to_templates(self, sample_cards):
        categorized = categorize_cards(sample_cards)
        packs = generate_card_packs(
            categorized=categorized, num_packs=2, pack_size=9, unseeded=True
        )
        templates = packs_to_templates(packs)
        assert len(templates) == 2
        for t in templates:
            assert t.total() == 9
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_packs.py::TestPacksToTemplates::test_converts_packs_to_templates -v`
Expected: FAIL with `ImportError: cannot import name 'packs_to_templates'`

**Step 3: Implement `packs_to_templates` and refactor `generate_grid_templates`**

Add to `src/cube_utils/packs.py` (before `generate_grid_templates`):

```python
def packs_to_templates(packs: list[list[Card]]) -> list[PackTemplate]:
    """Convert card packs into PackTemplates by counting categories.

    Args:
        packs: List of packs, where each pack is a list of Card.

    Returns:
        List of PackTemplate with per-category counts matching each pack.
    """
    templates: list[PackTemplate] = []
    for pack in packs:
        categorized_pack = categorize_cards(pack)
        template = PackTemplate(
            **{attr: len(categorized_pack[cat]) for attr, cat in _ATTR_TO_CATEGORY.items()}
        )
        templates.append(template)
    return templates
```

Then refactor `generate_grid_templates` to use it. Replace the per-pool loop (lines 210-219) with:

```python
    for i in range(num_pools):
        packs_for_pool = packs[i * num_grids : (i + 1) * num_grids]
        pool_template_list = packs_to_templates(packs_for_pool)

        pool = PackTemplate(**dict.fromkeys(_ATTR_TO_CATEGORY, 0))
        for t in pool_template_list:
            for attr in _ATTR_TO_CATEGORY:
                setattr(pool, attr, getattr(pool, attr) + getattr(t, attr))
        pool_templates.append(pool)
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_packs.py::TestPacksToTemplates tests/test_packs.py::TestGenerateGridTemplates -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add src/cube_utils/packs.py tests/test_packs.py
git commit --no-gpg-sign -m "refactor: extract packs_to_templates helper from grid template logic"
```

---

### Task 2: Add unseeded template mode tests

**Files:**
- Test: `tests/test_packs.py`

**Step 1: Write the failing tests**

Add to `tests/test_packs.py`:

```python
class TestUnseededTemplateCLI:
    """Tests for --unseeded flag in template mode."""

    def test_unseeded_template_mode_succeeds(self, tmp_path):
        csv_path = tmp_path / "cube.csv"
        _write_sample_cube_csv(csv_path)
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["packs", "--cube", str(csv_path), "--unseeded", "--players", "2", "--packs", "1"],
        )
        assert result.exit_code == 0
        assert "Player 1" in result.output
        assert "Player 2" in result.output

    def test_unseeded_template_totals_correct(self, tmp_path):
        csv_path = tmp_path / "cube.csv"
        _write_sample_cube_csv(csv_path)
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["packs", "--cube", str(csv_path), "--unseeded", "--players", "2", "--packs", "1"],
        )
        assert result.exit_code == 0
        # Should contain category labels like seeded mode
        assert "multi" in result.output
        assert "land" in result.output

    def test_unseeded_arbitrary_pack_size(self, tmp_path):
        csv_path = tmp_path / "cube.csv"
        _write_sample_cube_csv(csv_path)
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "packs", "--cube", str(csv_path), "--unseeded",
                "--players", "2", "--packs", "1", "--pack-size", "13",
            ],
        )
        assert result.exit_code == 0
        assert "Player 1" in result.output

    def test_unseeded_varies_from_seeded(self, tmp_path):
        """Unseeded packs should not always have exactly 1 fixing card."""
        import random
        csv_path = tmp_path / "cube.csv"
        _write_sample_cube_csv(csv_path)
        runner = CliRunner()

        # Run multiple times and check that fixing count varies
        fixing_counts = set()
        for seed in range(20):
            random.seed(seed)
            result = runner.invoke(
                main,
                ["packs", "--cube", str(csv_path), "--unseeded", "--players", "1", "--packs", "1"],
            )
            assert result.exit_code == 0
            # Parse fixing count from output like "1fixing"
            import re
            match = re.search(r"(\d+)fixing", result.output)
            assert match is not None
            fixing_counts.add(int(match.group(1)))

        # With proportional distribution, fixing should vary (not always 1)
        assert len(fixing_counts) > 1, f"Fixing count was always {fixing_counts}"
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_packs.py::TestUnseededTemplateCLI -v`
Expected: Some tests fail because unseeded in template mode currently ignores the flag

**Step 3: (Implementation in Task 3)**

---

### Task 3: Wire up unseeded template mode in `cli.py`

**Files:**
- Modify: `src/cube_utils/cli.py:165-219`
- Modify: `src/cube_utils/packs.py` (export `packs_to_templates`)

**Step 1: Update the CLI to support unseeded template mode**

In `src/cube_utils/cli.py`, modify the packs function (starting at line 171):

Replace:
```python
    # Validate pack size
    try:
        get_pack_structure(pack_size)
    except ValueError as e:
        raise click.ClickException(str(e)) from None
```

With:
```python
    # Validate pack size (only needed for seeded mode)
    if not unseeded:
        try:
            get_pack_structure(pack_size)
        except ValueError as e:
            raise click.ClickException(str(e)) from None
```

Then modify the template mode `else` branch (line 206). Replace:
```python
    else:
        templates = generate_pack_templates(num_packs=total_packs, pack_size=pack_size)
```

With:
```python
    else:
        if unseeded:
            all_packs = generate_card_packs(
                categorized=categorized,
                num_packs=total_packs,
                pack_size=pack_size,
                unseeded=True,
            )
            templates = packs_to_templates(all_packs)
        else:
            templates = generate_pack_templates(num_packs=total_packs, pack_size=pack_size)
```

Add `packs_to_templates` to the imports from `cube_utils.packs`.

**Step 2: Run all tests to verify they pass**

Run: `uv run pytest tests/test_packs.py -v`
Expected: All PASS

**Step 3: Run linting**

Run: `uv run ruff check src/ tests/`
Expected: No errors

**Step 4: Commit**

```bash
git add src/cube_utils/cli.py tests/test_packs.py
git commit --no-gpg-sign -m "feat: support --unseeded flag in template mode with proportional category counts"
```

---

### Task 4: Verify end-to-end and clean up

**Step 1: Run full test suite**

Run: `uv run pytest -v`
Expected: All PASS

**Step 2: Run formatting**

Run: `uv run ruff format src/ tests/`

**Step 3: Manual smoke test**

Run: `uv run cube-utils packs --cube regular-cube.csv --players 8 --unseeded`
Expected: Output shows varying category counts per pack (not always 1fixing, 2-3multi, 2-3land)

Run: `uv run cube-utils packs --cube regular-cube.csv --players 8`
Expected: Output shows seeded templates (unchanged behavior)

Run: `uv run cube-utils packs --cube regular-cube.csv --players 2 --unseeded --pack-size 13`
Expected: Succeeds with 13-card packs

**Step 4: Final commit if any formatting changes**

```bash
git add -u && git commit --no-gpg-sign -m "style: format"
```
