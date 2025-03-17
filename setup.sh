#!/bin/bash

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Função para verificar erros
check_error() {
    if [ $? -ne 0 ]; then
        echo -e "${RED}Erro: $1${NC}"
        exit 1
    fi
}

echo -e "${YELLOW}Iniciando instalação do Sistema de Monitoramento...${NC}"

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Por favor, execute como root${NC}"
    exit 1
fi

# Atualizar sistema
echo -e "${YELLOW}Atualizando sistema...${NC}"
apt update && apt upgrade -y
check_error "Falha ao atualizar sistema"

# Instalar dependências do sistema
echo -e "${YELLOW}Instalando dependências...${NC}"
apt install -y python3-pip python3-venv git build-essential libgl1-mesa-glx libglib2.0-0 mailutils
check_error "Falha ao instalar dependências"

# Criar diretório do projeto
echo -e "${YELLOW}Criando diretórios...${NC}"
mkdir -p /opt/sistema-monitoramento
mkdir -p /backup/monitoramento
cd /opt/sistema-monitoramento
check_error "Falha ao criar diretórios"

# Criar ambiente virtual
echo -e "${YELLOW}Criando ambiente virtual...${NC}"
python3 -m venv venv
source venv/bin/activate
check_error "Falha ao criar ambiente virtual"

# Instalar dependências Python
echo -e "${YELLOW}Instalando dependências Python...${NC}"
pip install -r requirements.txt
check_error "Falha ao instalar dependências Python"

# Criar diretórios necessários
echo -e "${YELLOW}Criando diretórios do sistema...${NC}"
mkdir -p gravacoes_suspeitas
mkdir -p logs
check_error "Falha ao criar diretórios do sistema"

# Configurar permissões
echo -e "${YELLOW}Configurando permissões...${NC}"
chown -R $SUDO_USER:$SUDO_USER /opt/sistema-monitoramento
chown -R $SUDO_USER:$SUDO_USER /backup/monitoramento
check_error "Falha ao configurar permissões"

# Criar serviço systemd
echo -e "${YELLOW}Configurando serviço systemd...${NC}"
tee /etc/systemd/system/monitoramento.service << EOF
[Unit]
Description=Sistema de Monitoramento de Furtos
After=network.target

[Service]
Type=simple
User=$SUDO_USER
WorkingDirectory=/opt/sistema-monitoramento
Environment=PATH=/opt/sistema-monitoramento/venv/bin
ExecStart=/opt/sistema-monitoramento/venv/bin/python detectar_movimento.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
check_error "Falha ao criar serviço systemd"

# Configurar backup automático
echo -e "${YELLOW}Configurando backup automático...${NC}"
chmod +x backup.sh
(crontab -l 2>/dev/null | grep -v "backup.sh"; echo "0 2 * * * /opt/sistema-monitoramento/backup.sh") | crontab -
check_error "Falha ao configurar backup"

# Configurar monitoramento de saúde
echo -e "${YELLOW}Configurando monitoramento de saúde...${NC}"
chmod +x monitor_health.sh
(crontab -l 2>/dev/null | grep -v "monitor_health.sh"; echo "*/15 * * * * /opt/sistema-monitoramento/monitor_health.sh") | crontab -
check_error "Falha ao configurar monitoramento"

# Recarregar systemd e iniciar serviço
echo -e "${YELLOW}Iniciando serviço...${NC}"
systemctl daemon-reload
systemctl enable monitoramento
systemctl start monitoramento
check_error "Falha ao iniciar serviço"

echo -e "${GREEN}Instalação concluída com sucesso!${NC}"
echo -e "${YELLOW}Comandos úteis:${NC}"
echo -e "Verificar status: systemctl status monitoramento"
echo -e "Ver logs: journalctl -u monitoramento -f"
echo -e "Reiniciar serviço: systemctl restart monitoramento"
echo -e "Parar serviço: systemctl stop monitoramento"
echo -e "Iniciar serviço: systemctl start monitoramento" 