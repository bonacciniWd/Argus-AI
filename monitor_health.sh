#!/bin/bash

# Configurações
LOG_FILE="/opt/sistema-monitoramento/logs/health_check.log"
ALERT_EMAIL="seu_email@exemplo.com"
THRESHOLD_CPU=80
THRESHOLD_MEM=80
THRESHOLD_DISK=85

# Função para enviar alerta
send_alert() {
    echo "$(date) - $1" >> $LOG_FILE
    echo "$1" | mail -s "Alerta do Sistema de Monitoramento" $ALERT_EMAIL
}

# Verificar uso de CPU
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d. -f1)
if [ $CPU_USAGE -gt $THRESHOLD_CPU ]; then
    send_alert "Alerta: Uso de CPU está em $CPU_USAGE%"
fi

# Verificar uso de memória
MEM_USAGE=$(free | grep Mem | awk '{print $3/$2 * 100.0}' | cut -d. -f1)
if [ $MEM_USAGE -gt $THRESHOLD_MEM ]; then
    send_alert "Alerta: Uso de memória está em $MEM_USAGE%"
fi

# Verificar uso de disco
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt $THRESHOLD_DISK ]; then
    send_alert "Alerta: Uso de disco está em $DISK_USAGE%"
fi

# Verificar status do serviço
if ! systemctl is-active --quiet monitoramento; then
    send_alert "Alerta: Serviço de monitoramento está inativo!"
fi

# Verificar conexão com DVR
if ! ping -c 1 $(cat /opt/sistema-monitoramento/config_dvr.json | grep -o '"host": "[^"]*"' | cut -d'"' -f4) > /dev/null; then
    send_alert "Alerta: Não foi possível conectar ao DVR!"
fi

# Limpar logs antigos
find /opt/sistema-monitoramento/logs -type f -mtime +30 -delete 