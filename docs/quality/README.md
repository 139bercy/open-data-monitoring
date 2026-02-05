# Metadata Quality Evaluation

## Overview

This module provides LLM-based automated evaluation of dataset metadata quality according to DCAT standards and the ministerial Open Data charter.

## Usage

### Evaluate a dataset

```bash
app quality evaluate <dataset-id> --dcat docs/quality/dcat_reference.md --charter docs/quality/charter_opendata.md
```

**Arguments:**
- `dataset-id`: UUID of the dataset to evaluate

**Options:**
- `--dcat`: Path to DCAT reference markdown (default: `docs/quality/dcat_reference.md`)
- `--charter`: Path to Open Data charter markdown (default: `docs/quality/charter_opendata.md`)
- `--model`: Ollama model to use (default: `llama3.1`)

### Example

```bash
app quality evaluate 550e8400-e29b-41d4-a716-446655440000 --model llama3.1
```

## Configuration

### Option 1: OpenAI (Recommended)

```bash
# Get API key from platform.openai.com/api-keys
export OPENAI_API_KEY="sk-your-key-here"
```

See [OPENAI_SETUP.md](OPENAI_SETUP.md) for detailed instructions.

### Option 2: Ollama (Local)

```bash
# macOS
brew install ollama
ollama serve
ollama pull llama3.1
```

See [OLLAMA_SETUP.md](OLLAMA_SETUP.md) for detailed instructions.

## Evaluation Criteria

### Descriptive Metadata (40%)
- **Title** (10%): Conciseness (5-10 words), clarity, business terms
- **Description** (15%): Completeness (300-500 chars), clarity, objective
- **Producer** (5%): Presence, correct format
- **Contact** (5%): Valid email, BALF preference
- **Keywords** (5%): Optimal count (3-7), relevance

### Administrative Metadata (30%)
- **Publication Date** (5%): Presence, consistency
- **License** (10%): Presence, validity (Licence Ouverte v2.0)
- **Update Date** (5%): Consistency with history
- **References** (10%): Valid URLs, relevance

### Geotemporal Metadata (30%)
- **Update Frequency** (10%): Presence, consistency
- **Spatial Coverage** (10%): Geographic precision
- **Temporal Coverage** (10%): Defined period, consistency

## Output

The evaluation provides:
- **Overall score** (0-100)
- **Criterion scores** by category
- **Issues** identified for each criterion
- **Suggestions** prioritized (high/medium/low)

## Reference Documents

- `dcat_reference.md`: DCAT vocabulary and best practices
- `charter_opendata.md`: Ministerial Open Data charter

You can customize these documents to match your organization's specific requirements.
