#!/bin/bash
# Installs the editing tools on a fresh machine. Safe to run more than once.
# (The cloud environment "eldailydad-editor" runs the same steps at session start.)
set -e
if [ ! -x /opt/whisper.cpp/build/bin/whisper-cli ]; then
  rm -rf /opt/whisper.cpp
  git clone --depth 1 https://github.com/ggml-org/whisper.cpp.git /opt/whisper.cpp
  cmake -S /opt/whisper.cpp -B /opt/whisper.cpp/build -DCMAKE_BUILD_TYPE=Release -DWHISPER_BUILD_TESTS=OFF > /dev/null
  cmake --build /opt/whisper.cpp/build -j"$(nproc)" --target whisper-cli > /dev/null
fi
if [ ! -s /opt/whisper.cpp/models/ggml-small.bin ]; then
  bash /opt/whisper.cpp/models/download-ggml-model.sh small > /dev/null
fi
command -v hyperframes > /dev/null || npm install -g hyperframes > /dev/null 2>&1
python3 -m pip install -q gdown numpy pillow 2> /dev/null || pip install -q gdown numpy pillow
echo "editing tools ready: $(/opt/whisper.cpp/build/bin/whisper-cli --help 2>&1 | head -0)whisper.cpp, hyperframes $(hyperframes --version 2>/dev/null), gdown $(python3 -c 'import gdown;print(gdown.__version__)')"
