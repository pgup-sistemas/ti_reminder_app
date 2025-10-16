"""
Serviço RFID para rastreamento automático de equipamentos
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from flask import current_app

from ..models import EquipmentRequest, db
from ..utils.timezone_utils import get_current_time_for_db

logger = logging.getLogger(__name__)


class RFIDService:
    """
    Serviço para integração com leitores RFID e rastreamento de equipamentos
    """

    # Simulação de leitores RFID conectados
    CONNECTED_READERS = {
        "reader_entrance": {"location": "Entrada Principal", "status": "online"},
        "reader_office_a": {"location": "Sala A", "status": "online"},
        "reader_office_b": {"location": "Sala B", "status": "online"},
        "reader_storage": {"location": "Depósito", "status": "online"},
        "reader_exit": {"location": "Saída", "status": "online"},
    }

    @staticmethod
    def scan_equipment(rfid_tag: str, reader_id: str) -> Dict:
        """
        Processa leitura RFID de um equipamento

        Args:
            rfid_tag: Tag RFID lida
            reader_id: ID do leitor que fez a leitura

        Returns:
            Dict com resultado da operação
        """
        try:
            # Buscar equipamento pela tag RFID
            equipment = EquipmentRequest.query.filter_by(rfid_tag=rfid_tag).first()

            if not equipment:
                logger.warning(f"Tag RFID não encontrada: {rfid_tag}")
                return {
                    "success": False,
                    "message": f"Equipamento com tag {rfid_tag} não encontrado",
                    "equipment": None
                }

            # Verificar se o leitor existe
            if reader_id not in RFIDService.CONNECTED_READERS:
                logger.error(f"Leitor RFID não reconhecido: {reader_id}")
                return {
                    "success": False,
                    "message": f"Leitor {reader_id} não autorizado",
                    "equipment": equipment
                }

            # Obter localização do leitor
            location = RFIDService.CONNECTED_READERS[reader_id]["location"]

            # Atualizar informações de rastreamento
            old_location = equipment.rfid_last_location
            equipment.rfid_last_location = location
            equipment.rfid_last_scan = get_current_time_for_db()
            equipment.rfid_reader_id = reader_id
            equipment.rfid_status = "ativo"

            # Verificar se houve mudança de localização
            location_changed = old_location != location

            # Salvar alterações
            db.session.commit()

            logger.info(f"Equipamento {equipment.id} ({rfid_tag}) detectado em {location}")

            return {
                "success": True,
                "message": f"Equipamento localizado em {location}",
                "equipment": equipment,
                "location_changed": location_changed,
                "old_location": old_location,
                "new_location": location,
                "reader_id": reader_id
            }

        except Exception as e:
            logger.error(f"Erro ao processar leitura RFID: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": f"Erro interno: {str(e)}",
                "equipment": None
            }

    @staticmethod
    def assign_rfid_tag(equipment_id: int, rfid_tag: str) -> Dict:
        """
        Atribui uma tag RFID a um equipamento

        Args:
            equipment_id: ID do equipamento
            rfid_tag: Tag RFID a ser atribuída

        Returns:
            Dict com resultado da operação
        """
        try:
            equipment = EquipmentRequest.query.get_or_404(equipment_id)

            # Verificar se a tag já está em uso
            existing = EquipmentRequest.query.filter_by(rfid_tag=rfid_tag).first()
            if existing and existing.id != equipment_id:
                return {
                    "success": False,
                    "message": f"Tag RFID já está atribuída ao equipamento {existing.id}"
                }

            # Atribuir tag
            equipment.rfid_tag = rfid_tag
            equipment.rfid_status = "ativo"
            equipment.rfid_last_scan = get_current_time_for_db()

            db.session.commit()

            logger.info(f"Tag RFID {rfid_tag} atribuída ao equipamento {equipment_id}")

            return {
                "success": True,
                "message": f"Tag RFID atribuída com sucesso",
                "equipment": equipment
            }

        except Exception as e:
            logger.error(f"Erro ao atribuir tag RFID: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": f"Erro interno: {str(e)}"
            }

    @staticmethod
    def remove_rfid_tag(equipment_id: int) -> Dict:
        """
        Remove a tag RFID de um equipamento

        Args:
            equipment_id: ID do equipamento

        Returns:
            Dict com resultado da operação
        """
        try:
            equipment = EquipmentRequest.query.get_or_404(equipment_id)

            old_tag = equipment.rfid_tag
            equipment.rfid_tag = None
            equipment.rfid_status = "desconhecido"
            equipment.rfid_last_location = None
            equipment.rfid_last_scan = None
            equipment.rfid_reader_id = None

            db.session.commit()

            logger.info(f"Tag RFID {old_tag} removida do equipamento {equipment_id}")

            return {
                "success": True,
                "message": f"Tag RFID removida com sucesso",
                "equipment": equipment
            }

        except Exception as e:
            logger.error(f"Erro ao remover tag RFID: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": f"Erro interno: {str(e)}"
            }

    @staticmethod
    def get_equipment_location(equipment_id: int) -> Dict:
        """
        Obtém a localização atual de um equipamento via RFID

        Args:
            equipment_id: ID do equipamento

        Returns:
            Dict com informações de localização
        """
        try:
            equipment = EquipmentRequest.query.get_or_404(equipment_id)

            if not equipment.rfid_tag:
                return {
                    "success": False,
                    "message": "Equipamento não possui tag RFID atribuída",
                    "location": None,
                    "last_scan": None
                }

            return {
                "success": True,
                "message": "Localização obtida com sucesso",
                "location": equipment.rfid_last_location,
                "last_scan": equipment.rfid_last_scan,
                "status": equipment.rfid_status,
                "reader_id": equipment.rfid_reader_id
            }

        except Exception as e:
            logger.error(f"Erro ao obter localização: {str(e)}")
            return {
                "success": False,
                "message": f"Erro interno: {str(e)}",
                "location": None,
                "last_scan": None
            }

    @staticmethod
    def get_lost_equipment() -> List[EquipmentRequest]:
        """
        Retorna lista de equipamentos marcados como perdidos ou não localizados

        Returns:
            Lista de equipamentos perdidos
        """
        try:
            # Equipamentos com status RFID "perdido" ou sem leitura há mais de 7 dias
            cutoff_date = get_current_time_for_db() - timedelta(days=7)

            lost_equipment = EquipmentRequest.query.filter(
                db.or_(
                    EquipmentRequest.rfid_status == "perdido",
                    db.and_(
                        EquipmentRequest.rfid_tag.isnot(None),
                        db.or_(
                            EquipmentRequest.rfid_last_scan.is_(None),
                            EquipmentRequest.rfid_last_scan < cutoff_date
                        )
                    )
                )
            ).all()

            return lost_equipment

        except Exception as e:
            logger.error(f"Erro ao buscar equipamentos perdidos: {str(e)}")
            return []

    @staticmethod
    def get_reader_status() -> Dict:
        """
        Retorna status de todos os leitores RFID conectados

        Returns:
            Dict com status dos leitores
        """
        return {
            "readers": RFIDService.CONNECTED_READERS,
            "total_readers": len(RFIDService.CONNECTED_READERS),
            "online_readers": sum(1 for r in RFIDService.CONNECTED_READERS.values() if r["status"] == "online"),
            "timestamp": get_current_time_for_db()
        }

    @staticmethod
    def simulate_rfid_scan(rfid_tag: str, reader_id: str) -> Dict:
        """
        Simula uma leitura RFID para testes/desenvolvimento

        Args:
            rfid_tag: Tag RFID a simular
            reader_id: ID do leitor

        Returns:
            Resultado da simulação
        """
        logger.info(f"SIMULAÇÃO: Leitura RFID - Tag: {rfid_tag}, Leitor: {reader_id}")

        # Pequeno delay para simular processamento
        time.sleep(0.1)

        return RFIDService.scan_equipment(rfid_tag, reader_id)

    @staticmethod
    def bulk_assign_rfid_tags(equipment_ids: List[int], rfid_tags: List[str]) -> Dict:
        """
        Atribui tags RFID em lote para múltiplos equipamentos

        Args:
            equipment_ids: Lista de IDs de equipamentos
            rfid_tags: Lista de tags RFID correspondentes

        Returns:
            Dict com resultado da operação em lote
        """
        if len(equipment_ids) != len(rfid_tags):
            return {
                "success": False,
                "message": "Número de equipamentos e tags deve ser igual"
            }

        results = []
        success_count = 0

        for equip_id, tag in zip(equipment_ids, rfid_tags):
            result = RFIDService.assign_rfid_tag(equip_id, tag)
            results.append({
                "equipment_id": equip_id,
                "rfid_tag": tag,
                "success": result["success"],
                "message": result["message"]
            })
            if result["success"]:
                success_count += 1

        return {
            "success": success_count == len(equipment_ids),
            "message": f"{success_count}/{len(equipment_ids)} tags atribuídas com sucesso",
            "results": results
        }