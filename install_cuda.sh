#!/bin/bash
# Install CUDA 12 and cuDNN 9 for faster-whisper GPU support
# Tested on Pop!_OS 22.04 / Ubuntu 22.04

set -e

echo "Installing CUDA 12 and cuDNN 9 for GPU transcription..."
echo ""

# Check if already installed
if ldconfig -p 2>/dev/null | grep -q "libcudnn_ops.so.9"; then
    echo "✓ cuDNN 9 is already installed"
    exit 0
fi

# Download and install CUDA keyring
echo "Adding NVIDIA repository..."
KEYRING_DEB="cuda-keyring_1.1-1_all.deb"
wget -q "https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/$KEYRING_DEB" -O "/tmp/$KEYRING_DEB"
sudo dpkg -i "/tmp/$KEYRING_DEB"
rm "/tmp/$KEYRING_DEB"

# Update package list
sudo apt update

# Install CUDA toolkit and cuDNN 9
echo "Installing CUDA 12 toolkit and cuDNN 9..."
sudo apt install -y cuda-toolkit-12-6 libcudnn9-cuda-12

# Add to PATH if not already there
CUDA_PATH_LINE='export PATH=/usr/local/cuda-12/bin:$PATH'
CUDA_LD_LINE='export LD_LIBRARY_PATH=/usr/local/cuda-12/lib64:$LD_LIBRARY_PATH'

if ! grep -q "cuda-12" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# CUDA 12" >> ~/.bashrc
    echo "$CUDA_PATH_LINE" >> ~/.bashrc
    echo "$CUDA_LD_LINE" >> ~/.bashrc
    echo "Added CUDA 12 to ~/.bashrc"
fi

# Export for current session
export PATH=/usr/local/cuda-12/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-12/lib64:$LD_LIBRARY_PATH

echo ""
echo "✅ CUDA 12 and cuDNN 9 installed!"
echo ""
echo "Please restart your terminal or run:"
echo "  source ~/.bashrc"
