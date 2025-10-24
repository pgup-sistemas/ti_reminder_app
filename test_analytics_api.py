"""
Script para testar APIs Analytics diretamente
"""
from app import create_app, db
from app.services.analytics.analytics_service import AnalyticsService
from datetime import date, timedelta

app = create_app()

with app.app_context():
    print("\n" + "="*60)
    print("TESTE DAS APIs ANALYTICS")
    print("="*60)
    
    try:
        # Teste 1: KPIs
        print("\n[1] Testando get_dashboard_kpis()...")
        kpis = AnalyticsService.get_dashboard_kpis()
        print(f"✅ Sucesso! KPIs: {kpis}")
    except Exception as e:
        print(f"❌ ERRO: {e}")
    
    try:
        # Teste 2: Chamados por período
        print("\n[2] Testando get_chamados_por_periodo()...")
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        chamados = AnalyticsService.get_chamados_por_periodo(start_date, end_date)
        print(f"✅ Sucesso! {len(chamados)} registros")
    except Exception as e:
        print(f"❌ ERRO: {e}")
    
    try:
        # Teste 3: Por prioridade
        print("\n[3] Testando get_chamados_por_prioridade()...")
        prioridade = AnalyticsService.get_chamados_por_prioridade()
        print(f"✅ Sucesso! {len(prioridade)} prioridades")
    except Exception as e:
        print(f"❌ ERRO: {e}")
    
    try:
        # Teste 4: Performance
        print("\n[4] Testando get_performance_por_tecnico()...")
        performance = AnalyticsService.get_performance_por_tecnico(start_date, end_date)
        print(f"✅ Sucesso! {len(performance)} técnicos")
    except Exception as e:
        print(f"❌ ERRO: {e}")
    
    try:
        # Teste 5: Por setor
        print("\n[5] Testando get_chamados_por_setor()...")
        setores = AnalyticsService.get_chamados_por_setor()
        print(f"✅ Sucesso! {len(setores)} setores")
    except Exception as e:
        print(f"❌ ERRO: {e}")
    
    print("\n" + "="*60)
    print("DIAGNÓSTICO COMPLETO")
    print("="*60 + "\n")
