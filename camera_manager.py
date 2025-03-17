import cv2
import json
import time
from typing import Optional, Dict, List

class CameraManager:
    def __init__(self, config_file: str = 'config_dvr.json'):
        self.config = self._load_config(config_file)
        self.cameras: Dict[int, cv2.VideoCapture] = {}
        self.last_reconnect: Dict[int, float] = {}
        self.reconnect_interval = 5  # segundos

    def _load_config(self, config_file: str) -> dict:
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception(f"Arquivo de configuração {config_file} não encontrado")

    def connect_camera(self, camera_id: int) -> bool:
        """Conecta a uma câmera específica"""
        camera_config = next((cam for cam in self.config['dvr']['cameras'] 
                            if cam['id'] == camera_id), None)
        
        if not camera_config:
            print(f"Câmera {camera_id} não encontrada na configuração")
            return False

        try:
            cap = cv2.VideoCapture(camera_config['rtsp_url'])
            if not cap.isOpened():
                print(f"Erro ao conectar com a câmera {camera_id}")
                return False

            self.cameras[camera_id] = cap
            self.last_reconnect[camera_id] = time.time()
            print(f"Câmera {camera_id} conectada com sucesso")
            return True

        except Exception as e:
            print(f"Erro ao conectar com a câmera {camera_id}: {str(e)}")
            return False

    def get_frame(self, camera_id: int) -> Optional[np.ndarray]:
        """Obtém um frame de uma câmera específica"""
        if camera_id not in self.cameras:
            if not self.connect_camera(camera_id):
                return None

        cap = self.cameras[camera_id]
        ret, frame = cap.read()

        if not ret:
            # Tenta reconectar se passou tempo suficiente
            if time.time() - self.last_reconnect[camera_id] > self.reconnect_interval:
                print(f"Tentando reconectar câmera {camera_id}")
                cap.release()
                if self.connect_camera(camera_id):
                    ret, frame = cap.read()
                else:
                    return None
            else:
                return None

        return frame

    def release_all(self):
        """Libera todas as conexões de câmera"""
        for cap in self.cameras.values():
            cap.release()
        self.cameras.clear()
        self.last_reconnect.clear()

    def get_camera_info(self, camera_id: int) -> Optional[dict]:
        """Retorna informações de configuração de uma câmera"""
        return next((cam for cam in self.config['dvr']['cameras'] 
                    if cam['id'] == camera_id), None) 