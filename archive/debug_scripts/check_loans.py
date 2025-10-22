from app import create_app, db
from app.models import EquipmentLoan, EquipmentReservation

def check_loans():
    app = create_app()
    with app.app_context():
        # Verificar empréstimos ativos
        active_loans = EquipmentLoan.query.filter_by(status='ativo').all()
        if active_loans:
            print("=== Empréstimos Ativos ===")
            for loan in active_loans:
                print(f"ID: {loan.id}, Equipamento: {loan.equipment.name}, " 
                      f"Usuário: {loan.user.username}, "
                      f"Data Empréstimo: {loan.loan_date}, "
                      f"Devolução Prevista: {loan.expected_return_date}, "
                      f"Status: {loan.status}")
        else:
            print("Nenhum empréstimo ativo encontrado.")
        
        # Verificar reservas confirmadas
        active_reservations = EquipmentReservation.query.filter_by(status='confirmada').all()
        if active_reservations:
            print("\n=== Reservas Confirmadas ===")
            for res in active_reservations:
                print(f"ID: {res.id}, Equipamento: {res.equipment.name}, "
                      f"Usuário: {res.user.username}, "
                      f"Período: {res.start_date} a {res.end_date}, "
                      f"Status: {res.status}")
        else:
            print("\nNenhuma reserva confirmada encontrada.")

if __name__ == "__main__":
    check_loans()
