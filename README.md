# Sistema de Monitoramento de Furtos em Supermercados

Sistema de detecção de furtos em supermercados usando visão computacional, integrado com DVR e câmeras IP.

## Autor

Desenvolvido por [Denis Bonaccini](https://github.com/bonacciniWd)

## Funcionalidades

- Detecção de pessoas e objetos
- Monitoramento de comportamentos suspeitos
- Gravação automática de incidentes
- Integração com DVR
- Upload para nuvem
- Sistema de alertas
- Monitoramento de saúde do sistema
- Backup automático

## Requisitos

- Python 3.8+
- OpenCV
- MediaPipe
- NumPy
- Outras dependências listadas em `requirements.txt`

## Instalação

1. Clone o repositório:
```bash
git clone [URL_DO_REPOSITORIO]
cd sistema-monitoramento
```

2. Execute o script de instalação como root:
```bash
sudo ./setup.sh
```

O script irá:
- Atualizar o sistema
- Instalar dependências necessárias
- Criar ambiente virtual Python
- Configurar o serviço systemd
- Configurar backup automático
- Configurar monitoramento de saúde
- Iniciar o serviço

## Configuração

1. Configure o arquivo `config_dvr.json` com as informações do seu DVR:
```json
{
    "dvr": {
        "host": "seu_dvr_ip",
        "port": 554,
        "username": "seu_usuario",
        "password": "sua_senha",
        "protocol": "rtsp"
    },
    "cameras": [
        {
            "id": 1,
            "name": "Entrada",
            "rtsp_url": "rtsp://usuario:senha@dvr_ip:554/Streaming/channels/101",
            "zona": "entrada"
        }
    ]
}
```

2. Configure o arquivo `config.json` com as configurações do sistema:
```json
{
    "confianca_minima": 0.5,
    "tempo_gravacao": 30,
    "tempo_suspeito": 5,
    "distancia_suspeita": 100
}
```

## Uso

### Comandos Básicos

1. Verificar status do serviço:
```bash
sudo systemctl status monitoramento
```

2. Ver logs em tempo real:
```bash
journalctl -u monitoramento -f
```

3. Reiniciar serviço:
```bash
sudo systemctl restart monitoramento
```

4. Parar serviço:
```bash
sudo systemctl stop monitoramento
```

5. Iniciar serviço:
```bash
sudo systemctl start monitoramento
```

### Manutenção

1. Atualizar o sistema:
```bash
sudo ./update.sh
```

2. Fazer backup manual:
```bash
sudo ./backup.sh
```

3. Verificar saúde do sistema:
```bash
sudo ./monitor_health.sh
```

## Estrutura de Arquivos

```
sistema-monitoramento/
├── detectar_movimento.py    # Script principal
├── config.json             # Configurações do sistema
├── config_dvr.json         # Configurações do DVR
├── requirements.txt        # Dependências Python
├── setup.sh               # Script de instalação
├── update.sh              # Script de atualização
├── backup.sh              # Script de backup
├── monitor_health.sh      # Script de monitoramento
├── gravacoes_suspeitas/   # Diretório de gravações
└── logs/                  # Diretório de logs
```

## Monitoramento e Alertas

O sistema inclui monitoramento automático de:
- Uso de CPU
- Uso de memória
- Uso de disco
- Status do serviço
- Conexão com DVR

Alertas são enviados por email quando:
- Uso de CPU > 80%
- Uso de memória > 80%
- Uso de disco > 85%
- Serviço inativo
- Falha na conexão com DVR

## Backup

Backups automáticos são realizados:
- Diariamente às 2h da manhã
- Retenção de 7 dias
- Inclui gravações e configurações
- Armazenados em `/backup/monitoramento`

## Suporte

Para suporte ou reportar problemas:
1. Verifique os logs em `/opt/sistema-monitoramento/logs`
2. Verifique o status do serviço
3. Abra uma issue no repositório

## Segurança

- Todas as senhas devem ser alteradas após a instalação
- Mantenha o sistema atualizado
- Faça backup regular das configurações
- Monitore os logs de acesso

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Contribuição

Contribuições são bem-vindas! Por favor, sinta-se à vontade para submeter um Pull Request.

1. Faça um Fork do projeto
2. Crie sua Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Contato

Denis Bonaccini - [@denisbonaccini](https://github.com/denisbonaccini)

Link do Projeto: [https://github.com/denisbonaccini/sistema-monitoramento-furtos](https://github.com/denisbonaccini/sistema-monitoramento-furtos) 