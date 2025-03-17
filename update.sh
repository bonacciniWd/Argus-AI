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

echo -e "${YELLOW}Iniciando atualização do Sistema de Monitoramento...${NC}"

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Por favor, execute como root${NC}"
    exit 1
fi

# Parar o serviço
echo -e "${YELLOW}Parando serviço...${NC}"
systemctl stop monitoramento
check_error "Falha ao parar serviço"

# Fazer backup das configurações
echo -e "${YELLOW}Fazendo backup das configurações...${NC}"
BACKUP_DIR="/backup/monitoramento/update_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cp /opt/sistema-monitoramento/config.json $BACKUP_DIR/
cp /opt/sistema-monitoramento/config_dvr.json $BACKUP_DIR/
check_error "Falha ao fazer backup"

# Atualizar código
echo -e "${YELLOW}Atualizando código...${NC}"
cd /opt/sistema-monitoramento
git pull
check_error "Falha ao atualizar código"

# Atualizar dependências Python
echo -e "${YELLOW}Atualizando dependências Python...${NC}"
source venv/bin/activate
pip install -r requirements.txt
check_error "Falha ao atualizar dependências"

# Restaurar configurações
echo -e "${YELLOW}Restaurando configurações...${NC}"
cp $BACKUP_DIR/config.json ./
cp $BACKUP_DIR/config_dvr.json ./
check_error "Falha ao restaurar configurações"

# Iniciar serviço
echo -e "${YELLOW}Iniciando serviço...${NC}"
systemctl start monitoramento
check_error "Falha ao iniciar serviço"

# Verificar status
echo -e "${YELLOW}Verificando status...${NC}"
systemctl status monitoramento

echo -e "${GREEN}Atualização concluída com sucesso!${NC}"
echo -e "${YELLOW}Para ver os logs: journalctl -u monitoramento -f${NC}" 