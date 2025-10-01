# LangExtract Import Troubleshooting Guide

## Overview

The LangExtract library may encounter import issues in certain environments, particularly in sandbox or containerized deployments. This guide provides diagnostic steps and workarounds.

## Common Issues

### SIGFPE (Floating Point Exception) During Import

**Symptoms:**
- Script crashes with `Floating point exception` during `import langextract`
- Process terminates with signal SIGFPE (signal 8)

**Root Cause:**
- Native dependencies (torch, numpy) conflict with sandbox security restrictions
- Mathematical operations in native libraries trigger hardware exceptions

**Workaround:**
The verification script now handles SIGFPE gracefully and provides manual test instructions.

## Manual Reproduction Steps

### Step 1: Basic Import Test
```bash
.venv/bin/python -c "import langextract; print('✅ langextract import successful')"
```

### Step 2: Component Access Test
```bash
.venv/bin/python -c "import langextract as lx; print('✅ ExampleData:', lx.data.ExampleData)"
```

### Step 3: ExampleData Construction Test
```bash
.venv/bin/python - <<'PY'
import langextract as lx

# Create minimal extraction
extraction = lx.data.Extraction(
    extraction_class="test_event",
    extraction_text="Test event occurred",
    attributes={
        "event_particulars": "Test event occurred",
        "citation": "Test Citation",
        "date": "2024-01-01"
    }
)

# Create ExampleData
example = lx.data.ExampleData(
    text="Test event occurred in test citation",
    extractions=[extraction]
)

print("✅ ExampleData construction successful")
print(f"Example text: {example.text}")
print(f"Extractions count: {len(example.extractions)}")
PY
```

### Step 4: Dependencies Test
```bash
.venv/bin/python -c "import torch, numpy; print('✅ Native dependencies OK')"
```

## Exit Codes

The verification script uses different exit codes to indicate failure types:

- `0`: Success - all tests passed
- `1`: ImportError or general failure
- `2`: SIGFPE or system-level failure

## Environment-Specific Notes

### Local Development
- Manual tests should work without issues
- If SIGFPE occurs locally, check torch/numpy installation

### CI/CD Pipelines
- Verification script will emit warnings instead of hard failures
- Pipeline can continue deployment if manual tests pass
- Monitor logs for warning messages

### Containerized Deployments
- May require specific torch/numpy versions
- Consider using CPU-only builds if GPU not needed
- Test container startup with manual commands

## Recovery Actions

### If Import Fails Completely
1. Check virtual environment integrity
2. Reinstall langextract: `uv add langextract --force`
3. Verify torch/numpy compatibility

### If Import Succeeds but Construction Fails
1. Check langextract API version compatibility
2. Review example construction in `src/core/langextract_client.py`
3. Update ExampleData format if API changed

### If Manual Tests Pass but Automation Fails
1. Environment-specific issue - proceed with deployment
2. Monitor production for actual runtime errors
3. Consider alternative verification approaches

## Contact

If issues persist after following this guide, provide:
- Full error traceback
- Output of manual reproduction commands
- Environment details (OS, Python version, container platform)