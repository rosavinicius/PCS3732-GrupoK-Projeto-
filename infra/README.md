# infra/

Arquivos de infraestrutura pra rodar o broker MQTT e o backend no Raspberry Pi.
Escolha **um** dos dois caminhos abaixo — não precisa dos dois.

## Opção A — systemd (recomendado para o Pi rodando "bare metal")

1. Instale o Mosquitto: `sudo apt install mosquitto mosquitto-clients`
2. Copie a config:
   ```
   sudo cp mosquitto/mosquitto.conf /etc/mosquitto/conf.d/irrigador.conf
   ```
3. Crie o usuário/senha do broker (usado pelo backend e por cada ESP32):
   ```
   sudo mosquitto_passwd -c /etc/mosquitto/passwd irrigador
   ```
4. Suba o broker:
   ```
   sudo systemctl enable --now mosquitto
   ```
5. Instale o serviço do backend (ajuste os caminhos dentro do arquivo se o
   seu usuário/pasta forem diferentes de `pi` / `/home/pi/irrigador-automatico`):
   ```
   sudo cp systemd/irrigador-backend.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now irrigador-backend
   ```
6. Acompanhar logs:
   ```
   journalctl -u irrigador-backend -f
   journalctl -u mosquitto -f
   ```

## Opção B — Docker Compose

Útil se você já usa Docker no Pi ou quer isolar tudo sem mexer no sistema.

```
docker compose -f infra/docker-compose.yml up -d
```

Antes de subir, gere o arquivo de senha do broker em `mosquitto/passwd`
(mesmo comando `mosquitto_passwd` acima, só que gerando o arquivo localmente
em vez de em `/etc/mosquitto/`) e crie `backend/.env` com as variáveis do
backend (porta, credenciais MQTT, etc).

## Importante: credenciais MQTT no firmware

Como `mosquitto.conf` desativa conexão anônima (`allow_anonymous false`), os
ESP32 também precisam se autenticar. Adicione ao `firmware/include/config.h`:

```cpp
#define MQTT_USERNAME "irrigador"
#define MQTT_PASSWORD "a_senha_que_voce_criou"
```

E troque, em `firmware/src/mqtt_client.cpp`, a chamada `client.connect(...)`
para passar `MQTT_USERNAME` e `MQTT_PASSWORD` no lugar dos dois `nullptr`.

## Portas usadas

| Serviço      | Porta | Observação                          |
|--------------|-------|--------------------------------------|
| Mosquitto    | 1883  | MQTT (ESP32 e backend)               |
| Backend      | 3000  | REST + WebSocket (dashboard)         |