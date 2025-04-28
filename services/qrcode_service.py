"""
Serviço de QR Code
Responsável por gerar QR codes para WhatsApp e outras funcionalidades.
"""
import os
import qrcode
from io import BytesIO

class QRCodeService:
    """Classe de serviço para geração de QR Codes."""
    
    TEMP_DIR = "temp_qrcodes"
    
    @classmethod
    def ensure_temp_dir(cls):
        """Garante que o diretório temporário para QR codes exista."""
        if not os.path.exists(cls.TEMP_DIR):
            os.makedirs(cls.TEMP_DIR)
    
    @staticmethod
    def create_whatsapp_url(phone_number):
        """
        Cria uma URL do WhatsApp a partir de um número de telefone.
        
        Args:
            phone_number (str): Número de telefone (formato: 5569999199509)
            
        Returns:
            str: URL do WhatsApp formatada
        """
        # Remover caracteres não numéricos
        clean_number = ''.join(c for c in phone_number if c.isdigit())
        
        # Certificar-se de que o número comece com 55 (Brasil)
        if not clean_number.startswith('55'):
            clean_number = '55' + clean_number
        
        return f"https://wa.me/{clean_number}"
    
    @classmethod
    def generate_whatsapp_qrcode(cls, phone_number, file_path=None):
        """
        Gera um QR code para WhatsApp.
        
        Args:
            phone_number (str): Número de telefone
            file_path (str, optional): Caminho para salvar o QR code. Se None, retorna o objeto de imagem.
            
        Returns:
            str ou Image: Caminho do arquivo salvo ou objeto de imagem
        """
        # Criar URL do WhatsApp
        whatsapp_url = cls.create_whatsapp_url(phone_number)
        
        # Criar QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(whatsapp_url)
        qr.make(fit=True)
        
        # Criar imagem
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Se for para salvar em arquivo
        if file_path:
            cls.ensure_temp_dir()
            img.save(file_path)
            return file_path
        
        # Caso contrário, retorna a imagem
        return img
    
    @classmethod
    def generate_whatsapp_qrcode_bytes(cls, phone_number):
        """
        Gera um QR code para WhatsApp e retorna os bytes.
        
        Args:
            phone_number (str): Número de telefone
            
        Returns:
            bytes: Bytes da imagem do QR code
        """
        # Criar URL do WhatsApp
        whatsapp_url = cls.create_whatsapp_url(phone_number)
        
        # Criar QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(whatsapp_url)
        qr.make(fit=True)
        
        # Criar imagem
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converter para bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        
        return img_bytes.getvalue()