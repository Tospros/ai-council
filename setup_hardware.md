# Hardware Setup Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Raspberry Pi (Frontend)                     │
│                     Django Web Application                       │
│                         Port 8000                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP Requests
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Jetson Nano Cluster                          │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │  Jetson #1    │ │  Jetson #2    │ │  Jetson #3    │         │
│  │ qwen2.5:1.5b  │ │deepseek-r1:1.5b│ │  gemma3:1b   │         │
│  │  (Attacker)   │ │  (Attacker)   │ │  (Attacker)  │         │
│  │  Ollama:11434 │ │  Ollama:11434 │ │  Ollama:11434│         │
│  └───────────────┘ └───────────────┘ └───────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Jailbreak Prompts
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Target Model (Raspberry Pi)                     │
│                       gemma3:1b                                  │
│                      Ollama:11434                                │
└─────────────────────────────────────────────────────────────────┘
```

## Jetson Nano Setup (x3)

### 1. Flash JetPack OS
- Download NVIDIA JetPack 4.6 or later
- Flash to SD card using Etcher

### 2. Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 3. Pull models
```bash
# Jetson 1
ollama pull qwen2.5:1.5b

# Jetson 2
ollama pull deepseek-r1:1.5b

# Jetson 3
ollama pull gemma3:1b
```

### 4. Configure Ollama for network access
```bash
# Edit systemd service
sudo systemctl edit ollama

# Add:
[Service]
Environment="OLLAMA_HOST=0.0.0.0"

# Restart
sudo systemctl restart ollama
```

### 5. Set static IP / hostname
Edit `/etc/hosts` on all devices:
```
192.168.1.101  jetson-nano-1.local
192.168.1.102  jetson-nano-2.local
192.168.1.103  jetson-nano-3.local
192.168.1.104  raspberry-pi.local
```

## Raspberry Pi Setup

### 1. Install Raspberry Pi OS (64-bit recommended)

### 2. Install Python 3.11+
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv
```

### 3. Install Ollama (for target model)
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma3:1b
```

### 4. Configure Ollama for network access
```bash
sudo systemctl edit ollama
# Add: Environment="OLLAMA_HOST=0.0.0.0"
sudo systemctl restart ollama
```

### 5. Clone and setup application
```bash
git clone <repo-url> llm_redteam
cd llm_redteam
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 6. Configure hosts
Edit `agents/config.py`:
```python
DEV_MODE = False  # Switch to production

ATTACKER_MODELS = [
    {
        "name": "qwen2.5:1.5b",
        "config": JetsonConfig(host="jetson-nano-1.local"),
        ...
    },
    ...
]
```

### 7. Initialize and run
```bash
python run.py init
python run.py run --host 0.0.0.0 --port 8000
```

## Network Requirements

- All devices on same subnet
- Ports open:
  - 11434 (Ollama) on all Jetsons and target Pi
  - 8000 (Django) on frontend Pi
- mDNS or static IPs configured

## Performance Notes

- Jetson Nano: ~1-2 tokens/sec for 1.5B models
- Raspberry Pi 4: ~0.5-1 tokens/sec for 1B models
- Consider using Jetson Orin Nano for better performance
- 4GB+ RAM recommended for 1.5B models
