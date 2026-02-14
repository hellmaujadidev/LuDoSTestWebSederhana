#!/data/data/com.termux/files/usr/bin/bash

# LuDos Installer for Termux
echo -e "\033[96m"
echo "██████╗ ██╗   ██╗██████╗  ██████╗ ███████╗"
echo "██╔══██╗██║   ██║██╔══██╗██╔═══██╗██╔════╝"
echo "██████╔╝██║   ██║██║  ██║██║   ██║███████╗"
echo "██╔══██╗██║   ██║██║  ██║██║   ██║╚════██║"
echo "██████╔╝╚██████╔╝██████╔╝╚██████╔╝███████║"
echo "╚═════╝  ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝"
echo -e "\033[0m"
echo "LuDos v0.1 Installer for Termux"
echo "Author: Luxifer"
echo ""

echo "[*] Updating packages..."
pkg update -y && pkg upgrade -y

echo "[*] Installing Python..."
pkg install python -y

echo "[*] Installing dependencies..."
pip install requests colorama

echo "[*] Creating directories..."
mkdir -p ~/ludos/{proxies,logs}

echo "[*] Downloading LuDos..."
curl -o ~/ludos/ludos.py https://raw.githubusercontent.com/luxifer/ludos/main/ludos.py

echo "[*] Creating launcher..."
cat > $PREFIX/bin/ludos << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/ludos
python ludos.py
EOF

chmod +x $PREFIX/bin/ludos

echo ""
echo -e "\033[92m[✓] Installation complete!{Fore.RESET}"
echo -e "\033[93m[!] Type 'ludos' to run the tool{Fore.RESET}"
echo ""