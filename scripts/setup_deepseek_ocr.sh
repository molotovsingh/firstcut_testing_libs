#!/bin/bash
# DeepSeek-OCR Installation Script
# Requires: CUDA 11.8+ GPU, conda/mamba

set -e

echo "🚀 DeepSeek-OCR Installation Script"
echo "===================================="
echo ""

# Check for CUDA
if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ ERROR: nvidia-smi not found"
    echo "   DeepSeek-OCR requires NVIDIA GPU with CUDA 11.8+"
    exit 1
fi

echo "✅ NVIDIA GPU detected:"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
echo ""

# Check CUDA version
CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}')
echo "📌 CUDA Version: $CUDA_VERSION"
echo ""

# Check for conda
if ! command -v conda &> /dev/null; then
    echo "❌ ERROR: conda not found"
    echo "   Install Miniconda: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo "✅ Conda detected: $(conda --version)"
echo ""

# Create environment
ENV_NAME="deepseek-ocr"
echo "📦 Creating conda environment: $ENV_NAME"
echo "   Python version: 3.12.9"
echo ""

read -p "⚠️  This will create/overwrite environment '$ENV_NAME'. Continue? [y/N] " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Installation cancelled"
    exit 1
fi

# Remove existing environment if present
if conda env list | grep -q "^$ENV_NAME "; then
    echo "🗑️  Removing existing environment: $ENV_NAME"
    conda env remove -n $ENV_NAME -y
fi

echo "🔧 Creating fresh environment..."
conda create -n $ENV_NAME python=3.12.9 -y
echo ""

# Activate environment
echo "🔌 Activating environment..."
eval "$(conda shell.bash hook)"
conda activate $ENV_NAME
echo ""

# Install PyTorch with CUDA 11.8
echo "📥 Installing PyTorch 2.6.0 with CUDA 11.8..."
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu118
echo ""

# Install transformers and tokenizers
echo "📥 Installing transformers and tokenizers..."
pip install transformers==4.46.3 tokenizers==0.20.3
echo ""

# Install dependencies
echo "📥 Installing additional dependencies..."
pip install einops addict easydict pillow PyMuPDF
echo ""

# Install flash-attn (may take a while)
echo "📥 Installing flash-attn 2.7.3 (this may take 5-10 minutes)..."
pip install flash-attn==2.7.3 --no-build-isolation
echo ""

# Verify installation
echo "🔍 Verifying installation..."
python3 << EOF
import torch
import transformers
import flash_attn

print(f"✅ PyTorch version: {torch.__version__}")
print(f"✅ CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"✅ CUDA version: {torch.version.cuda}")
    print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
    print(f"✅ GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
print(f"✅ Transformers version: {transformers.__version__}")
print(f"✅ Flash Attention installed")
EOF
echo ""

# Clone DeepSeek-OCR repository (optional, for examples)
echo "📥 Cloning DeepSeek-OCR repository (optional)..."
read -p "Clone DeepSeek-OCR repo for examples? [y/N] " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    REPO_DIR="$HOME/DeepSeek-OCR"
    if [ -d "$REPO_DIR" ]; then
        echo "⚠️  Directory $REPO_DIR already exists, skipping clone"
    else
        git clone https://github.com/deepseek-ai/DeepSeek-OCR.git "$REPO_DIR"
        echo "✅ Repository cloned to: $REPO_DIR"
    fi
fi
echo ""

# Download model (optional)
echo "📥 Pre-downloading DeepSeek-OCR model (optional, ~6GB)..."
echo "   Model will auto-download on first use if skipped"
read -p "Download model now? [y/N] " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 << 'EOF'
from transformers import AutoModel, AutoTokenizer
import os

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
model_name = "deepseek-ai/DeepSeek-OCR"

print("📥 Downloading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

print("📥 Downloading model (~6GB, may take several minutes)...")
model = AutoModel.from_pretrained(
    model_name,
    attn_implementation='flash_attention_2',
    trust_remote_code=True,
    use_safetensors=True
)

print("✅ Model downloaded and cached")
EOF
fi
echo ""

echo "✅ DeepSeek-OCR installation complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Activate environment: conda activate $ENV_NAME"
echo "   2. Run test script: python scripts/test_deepseek_ocr.py"
echo "   3. See docs/deepseek_ocr_setup.md for usage examples"
echo ""
echo "💡 Tips:"
echo "   - Model auto-downloads on first use (~6GB)"
echo "   - Requires ~4GB GPU memory for inference"
echo "   - Processing speed: ~2-3s per page on A100-40G"
echo ""
