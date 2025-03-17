#!/bin/bash

# Configurações
BACKUP_DIR="/backup/monitoramento"
DATA=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Criar diretório de backup se não existir
mkdir -p $BACKUP_DIR

# Backup das gravações
echo "Iniciando backup das gravações..."
tar -czf $BACKUP_DIR/gravacoes_$DATA.tar.gz /opt/sistema-monitoramento/gravacoes_suspeitas/

# Backup das configurações
echo "Iniciando backup das configurações..."
cp /opt/sistema-monitoramento/config_dvr.json $BACKUP_DIR/config_$DATA.json
cp /opt/sistema-monitoramento/config.json $BACKUP_DIR/config_sistema_$DATA.json

# Remover backups antigos
echo "Removendo backups antigos..."
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

# Verificar espaço em disco
echo "Verificando espaço em disco..."
df -h $BACKUP_DIR

echo "Backup concluído!" 