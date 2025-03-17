import cv2 
import numpy as np
import time
import mediapipe as mp
import os
from datetime import datetime
from collections import deque, defaultdict
import math

# Inicializar o MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

# Carrega os nomes das classes
try:
    with open('coco.names', 'r') as f:
        classes = [line.strip() for line in f.readlines()]
except FileNotFoundError:
    print("Erro: Arquivo coco.names não encontrado")
    exit()

# Carrega a configuração e os pesos do modelo
try:
    net = cv2.dnn.readNet('yolov4-tiny.weights', 'yolov4-tiny.cfg')
except cv2.error as e:
    print("Erro ao carregar os arquivos do YOLO:", e)
    exit()

# Define a camada de saída do modelo
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

# Captura de vídeo da câmera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Erro ao abrir a câmera 0, tentando câmera 1...")
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        print("Erro ao abrir a câmera 1, tentando câmera 2...")
        cap = cv2.VideoCapture(2)
        if not cap.isOpened():
            print("Nenhuma câmera disponível!")
            exit()

# Para rastrear as pessoas e as bolsas
person_boxes = []
bag_boxes = []
last_suspicious_time = 0

# Definir cores (BGR format - IMPORTANTE: OpenCV usa BGR, não RGB)
COR_PESSOA = (51, 51, 255)     # Vermelho mais vivo
COR_SUSPEITO = (0, 128, 255)   # Laranja mais vivo
COR_NORMAL = (0, 255, 0)       # Verde
COR_ALERTA = (0, 0, 255)       # Vermelho para alertas
COR_MAOS = (255, 198, 130)     # Azul claro para as mãos

# Dicionário de tradução de objetos
traducoes = {
    # Pessoas
    "person": "pessoa",
    
    # Objetos pessoais (potenciais locais de ocultação)
    "backpack": "mochila",
    "handbag": "bolsa",
    "suitcase": "mala",
    "umbrella": "guarda-chuva",
    
    # Produtos comuns de supermercado
    "bottle": "garrafa",
    "wine glass": "taça",
    "cup": "copo",
    "bowl": "tigela",
    "banana": "banana",
    "apple": "maçã",
    "sandwich": "sanduíche",
    "orange": "laranja",
    "broccoli": "brócolis",
    "carrot": "cenoura",
    "hot dog": "cachorro-quente",
    "pizza": "pizza",
    "donut": "rosquinha",
    "cake": "bolo"
}

# Objetos que merecem atenção especial
objetos_suspeitos = ["backpack", "handbag", "suitcase", "umbrella"]

# Definir níveis de alerta
TEMPO_SUSPEITO = 3  # segundos
DISTANCIA_SUSPEITA = 50  # pixels

# Classe para gravação de vídeo
class GravadorVideo:
    def __init__(self):
        self.output = None
        self.gravando = False
        self.diretorio = 'gravacoes_suspeitas'
        
        # Criar diretório se não existir
        if not os.path.exists(self.diretorio):
            os.makedirs(self.diretorio)
    
    def iniciar_gravacao(self, width, height):
        if not self.gravando:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.diretorio, f"suspeito_{timestamp}.avi")
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.output = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))
            self.gravando = True
    
    def gravar_frame(self, frame):
        if self.gravando:
            self.output.write(frame)
    
    def parar_gravacao(self):
        if self.gravando:
            self.output.release()
            self.gravando = False

# Adicionar após as definições de cores existentes
TEMPO_GRAVACAO = 10  # segundos para continuar gravando após um alerta

# Inicializar o gravador
gravador = GravadorVideo()
ultimo_alerta = 0

# Adicionar após as definições de cores
class DetectorVarredura:
    def __init__(self):
        self.historico_maos = deque(maxlen=30)  # Mantém histórico de 30 frames
        self.zona_caixa = None
        self.movimentos_suspeitos = 0
        self.ultimo_alerta = 0
        self.TEMPO_ENTRE_ALERTAS = 3  # segundos
        
    def definir_zona_caixa(self, x, y, w, h):
        self.zona_caixa = {
            'x1': x,
            'y1': y,
            'x2': x + w,
            'y2': y + h
        }
    
    def calcular_velocidade(self, pos_atual, pos_anterior):
        if not pos_anterior:
            return 0
        dx = pos_atual[0] - pos_anterior[0]
        dy = pos_atual[1] - pos_anterior[1]
        return math.sqrt(dx*dx + dy*dy)
    
    def detectar_varredura(self, hand_landmarks, width, height, current_time):
        if not self.zona_caixa:
            # Definir zona do caixa como região inferior da tela
            self.definir_zona_caixa(
                int(width * 0.1),    # 10% da largura
                int(height * 0.6),   # 60% da altura
                int(width * 0.8),    # 80% da largura
                int(height * 0.4)    # 40% da altura
            )
        
        # Obter posição da mão
        hand_x = int(hand_landmarks.landmark[9].x * width)
        hand_y = int(hand_landmarks.landmark[9].y * height)
        
        # Verificar se a mão está na zona do caixa
        if (self.zona_caixa['x1'] <= hand_x <= self.zona_caixa['x2'] and
            self.zona_caixa['y1'] <= hand_y <= self.zona_caixa['y2']):
            
            # Adicionar posição ao histórico
            self.historico_maos.append((hand_x, hand_y, current_time))
            
            # Analisar movimento
            if len(self.historico_maos) >= 10:
                velocidades = []
                direcoes_x = []
                
                # Calcular velocidades e direções
                for i in range(1, len(self.historico_maos)):
                    pos_atual = self.historico_maos[i]
                    pos_anterior = self.historico_maos[i-1]
                    
                    velocidade = self.calcular_velocidade(
                        (pos_atual[0], pos_atual[1]),
                        (pos_anterior[0], pos_anterior[1])
                    )
                    velocidades.append(velocidade)
                    
                    # Registrar direção do movimento
                    direcao_x = 1 if pos_atual[0] > pos_anterior[0] else -1
                    direcoes_x.append(direcao_x)
                
                # Detectar padrão de varredura
                mudancas_direcao = sum(1 for i in range(1, len(direcoes_x))
                                     if direcoes_x[i] != direcoes_x[i-1])
                
                velocidade_media = sum(velocidades) / len(velocidades)
                
                # Condições para varredura suspeita
                if (mudancas_direcao <= 2 and  # Movimento consistente
                    velocidade_media > 5 and    # Movimento rápido
                    current_time - self.ultimo_alerta > self.TEMPO_ENTRE_ALERTAS):
                    
                    self.ultimo_alerta = current_time
                    return True, "Possível varredura de produtos detectada"
        
        return False, ""

# Inicializar o detector de varredura após as outras inicializações
detector_varredura = DetectorVarredura()

class DetectorTrocaProdutos:
    def __init__(self):
        self.tempo_interacao = defaultdict(float)
        self.produtos_proximos = defaultdict(list)
        self.ultimo_alerta = 0
        self.TEMPO_SUSPEITO = 5  # segundos analisando dois produtos
        self.DISTANCIA_PRODUTOS = 100  # pixels
        
    def calcular_distancia(self, box1, box2):
        # Centro do primeiro box
        c1_x = box1[0] + box1[2]/2
        c1_y = box1[1] + box1[3]/2
        # Centro do segundo box
        c2_x = box2[0] + box2[2]/2
        c2_y = box2[1] + box2[3]/2
        
        return math.sqrt((c1_x - c2_x)**2 + (c1_y - c2_y)**2)
    
    def detectar_troca(self, produtos_detectados, hand_landmarks, width, height, current_time):
        if not produtos_detectados or not hand_landmarks:
            return False, ""
            
        hand_x = int(hand_landmarks.landmark[9].x * width)
        hand_y = int(hand_landmarks.landmark[9].y * height)
        
        produtos_proximos_maos = []
        
        # Verificar produtos próximos às mãos
        for produto_id, (x, y, w, h, label) in enumerate(produtos_detectados):
            centro_x = x + w/2
            centro_y = y + h/2
            distancia = math.sqrt((centro_x - hand_x)**2 + (centro_y - hand_y)**2)
            
            if distancia < self.DISTANCIA_PRODUTOS:
                produtos_proximos_maos.append((produto_id, label, (x, y, w, h)))
        
        # Se há dois ou mais produtos próximos às mãos
        if len(produtos_proximos_maos) >= 2:
            produtos_key = tuple(sorted([p[1] for p in produtos_proximos_maos]))
            
            # Verificar se os produtos estão próximos entre si
            for i in range(len(produtos_proximos_maos)):
                for j in range(i+1, len(produtos_proximos_maos)):
                    prod1 = produtos_proximos_maos[i]
                    prod2 = produtos_proximos_maos[j]
                    
                    if self.calcular_distancia(prod1[2], prod2[2]) < self.DISTANCIA_PRODUTOS:
                        # Atualizar tempo de interação
                        if produtos_key in self.tempo_interacao:
                            tempo_total = current_time - self.tempo_interacao[produtos_key]
                            
                            if (tempo_total > self.TEMPO_SUSPEITO and 
                                current_time - self.ultimo_alerta > 10):  # 10 segundos entre alertas
                                self.ultimo_alerta = current_time
                                return True, f"Possível troca de produtos detectada: {prod1[1]} e {prod2[1]}"
                        else:
                            self.tempo_interacao[produtos_key] = current_time
                            
        # Limpar interações antigas
        self.tempo_interacao = {k:v for k,v in self.tempo_interacao.items() 
                              if current_time - v < self.TEMPO_SUSPEITO + 5}
        
        return False, ""

# Inicializar o detector após as outras inicializações
detector_troca = DetectorTrocaProdutos()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Erro ao capturar o frame da câmera.")
        break

    # Inverter o frame horizontalmente (espelho)
    frame = cv2.flip(frame, 1)  # 1 para flip horizontal, 0 para vertical, -1 para ambos

    height, width, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Processar imagem com MediaPipe para detecção de mãos
    hand_results = hands.process(rgb_frame)

    # Converter frame para o modelo YOLO
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    class_ids = []
    confidences = []
    boxes = []

    # Detecção de objetos
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

    # Resetar caixas
    person_boxes.clear()
    bag_boxes.clear()

    # Lista para armazenar produtos detectados
    produtos_detectados = []

    # Armazenar as detecções
    if len(indexes) > 0:
        for i in indexes.flatten():
            x, y, w, h = boxes[i]
            label = str(classes[class_ids[i]])
            label_pt = traducoes.get(label, label)

            # Definir cor baseada no tipo de objeto
            if label == "person":
                cor = COR_PESSOA
                person_boxes.append((x, y, w, h))
            elif label in objetos_suspeitos:
                cor = COR_SUSPEITO
                bag_boxes.append((x, y, w, h))
            else:
                cor = COR_NORMAL

            # Desenhar retângulo e label
            cv2.rectangle(frame, (x, y), (x + w, y + h), cor, 2)
            cv2.putText(frame, label_pt, (x, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, cor, 2)

            # Armazenar produtos detectados (excluindo pessoas e objetos suspeitos)
            if label not in ["person"] + objetos_suspeitos:
                produtos_detectados.append((x, y, w, h, label))

    # Verificar comportamentos suspeitos
    comportamento_suspeito = False
    if hand_results.multi_hand_landmarks:
        for hand_landmarks in hand_results.multi_hand_landmarks:
            # Desenhar as mãos com a nova cor
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(color=COR_MAOS, thickness=2, circle_radius=2),
                mp_draw.DrawingSpec(color=COR_MAOS, thickness=2)
            )

            hand_x = int(hand_landmarks.landmark[9].x * width)
            hand_y = int(hand_landmarks.landmark[9].y * height)

            # Adicionar detecção de varredura
            varredura_detectada, mensagem = detector_varredura.detectar_varredura(
                hand_landmarks, width, height, time.time()
            )
            
            if varredura_detectada:
                # Desenhar zona do caixa
                cv2.rectangle(frame, 
                            (detector_varredura.zona_caixa['x1'], 
                             detector_varredura.zona_caixa['y1']),
                            (detector_varredura.zona_caixa['x2'], 
                             detector_varredura.zona_caixa['y2']),
                            COR_ALERTA, 2)
                
                # Mostrar alerta
                cv2.putText(frame, "ALERTA: " + mensagem,
                          (50, 120), cv2.FONT_HERSHEY_SIMPLEX,
                          0.8, COR_ALERTA, 2)
                
                # Iniciar gravação se não estiver gravando
                if not gravador.gravando:
                    gravador.iniciar_gravacao(width, height)
                ultimo_alerta = time.time()

            # Adicionar detecção de troca de produtos
            troca_detectada, mensagem_troca = detector_troca.detectar_troca(
                produtos_detectados,
                hand_landmarks,  # Agora passando o objeto hand_landmarks correto
                width,
                height,
                time.time()
            )
            
            if troca_detectada:
                # Mostrar alerta de troca
                cv2.putText(frame, "ALERTA: " + mensagem_troca,
                          (50, 150), cv2.FONT_HERSHEY_SIMPLEX,
                          0.8, COR_ALERTA, 2)
                
                # Iniciar gravação
                if not gravador.gravando:
                    gravador.iniciar_gravacao(width, height)
                ultimo_alerta = time.time()

            # Verificar interações suspeitas
            for bx, by, bw, bh in bag_boxes:
                distance_x = abs(bx + bw // 2 - hand_x)
                distance_y = abs(by + bh // 2 - hand_y)

                if distance_x < DISTANCIA_SUSPEITA and distance_y < DISTANCIA_SUSPEITA:
                    current_time = time.time()
                    if current_time - last_suspicious_time > TEMPO_SUSPEITO:
                        last_suspicious_time = current_time
                        ultimo_alerta = current_time
                        comportamento_suspeito = True
                        
                        # Mensagens de alerta com cor vermelha
                        cv2.putText(frame, "ALERTA: Possível ocultação de produto!", 
                                  (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, COR_ALERTA, 2)
                        cv2.putText(frame, "Verificar câmera " + str(int(cap.get(cv2.CAP_PROP_POS_FRAMES))), 
                                  (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, COR_ALERTA, 2)
                        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), COR_ALERTA, 3)

    # Gerenciar gravação
    if gravador.gravando:
        gravador.gravar_frame(frame)
        # Parar gravação se passou tempo suficiente desde o último alerta
        if time.time() - ultimo_alerta > TEMPO_GRAVACAO and not comportamento_suspeito:
            gravador.parar_gravacao()

    # Exibe o vídeo
    cv2.imshow('Sistema de Monitoramento - Supermercado', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Adicionar antes de finalizar o programa
gravador.parar_gravacao()
cap.release()
cv2.destroyAllWindows()
