# Ollama Setup Guide

## Installation

### macOS
```bash
# Install Ollama
brew install ollama

# Start Ollama service
ollama serve
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
```

### Windows
Download from [ollama.com](https://ollama.com/download)

## Pull recommended model

```bash
# Llama 3.1 (8B) - Recommended for quality evaluation
ollama pull llama3.1

# Alternative: Smaller/faster model
ollama pull llama3.2

# Alternative: Larger/better model (requires more RAM)
ollama pull llama3.1:70b
```

## Verify installation

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Test generation
ollama run llama3.1 "Hello, how are you?"
```

## Usage in the app

```bash
# Use default model (llama3.1)
app quality evaluate <dataset-id>

# Use specific model
app quality evaluate <dataset-id> --model llama3.2
```

## Troubleshooting

### "Ollama not reachable"
- Make sure `ollama serve` is running
- Check port 11434 is not blocked

### "Model not found"
- Pull the model: `ollama pull llama3.1`

### Slow inference
- Use a smaller model: `--model llama3.2`
- Reduce context in prompts (edit `prompts.py`)

## Model comparison

| Model | Size | RAM | Speed | Quality |
|-------|------|-----|-------|---------|
| llama3.2 | 3B | 4GB | Fast | Good |
| llama3.1 | 8B | 8GB | Medium | Excellent |
| llama3.1:70b | 70B | 64GB | Slow | Best |
