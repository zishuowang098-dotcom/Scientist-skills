#!/bin/bash
# macOS：双击运行（首次需在终端执行 chmod +x start-mac.command）
cd "$(dirname "$0")"
python3 bridge.py --port 8765 --workdir "$HOME/ScienceMentor"
