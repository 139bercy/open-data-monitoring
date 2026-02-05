# OpenAI Setup Guide

## Get API Key

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

## Set Environment Variable

```bash
# Add to your .env file
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# Or export directly
export OPENAI_API_KEY="sk-your-key-here"
```

## Install dependency

```bash
pip install openai
```

## Usage

```bash
# Default: OpenAI with gpt-4o-mini
app quality evaluate <dataset-id>

# Specify model
app quality evaluate <dataset-id> --model gpt-4o

# Use Ollama instead
app quality evaluate <dataset-id> --provider ollama
```

## Pricing (as of 2026)

| Model | Input | Output | Cost per eval |
|-------|-------|--------|---------------|
| gpt-4o-mini | $0.15/1M tokens | $0.60/1M tokens | ~$0.001 |
| gpt-4o | $2.50/1M tokens | $10/1M tokens | ~$0.02 |
| gpt-3.5-turbo | $0.50/1M tokens | $1.50/1M tokens | ~$0.003 |

**Recommended**: `gpt-4o-mini` for best quality/price ratio.

## Advantages

✅ **Fast**: 2-3 seconds per evaluation  
✅ **Reliable**: Excellent JSON mode  
✅ **Quality**: Better than local models  
✅ **Cheap**: ~$0.001 per evaluation
