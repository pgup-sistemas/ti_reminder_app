"""
Rotas de exportação para Analytics Dashboard
"""
from datetime import date, timedelta
from flask import Blueprint, request, send_file
from app.auth_utils import login_required

analytics_bp = Blueprint('analytics_export', __name__)


@analytics_bp.route("/api/analytics/export/excel")
@login_required
def export_excel():
    """Exporta os dados atuais do dashboard Analytics em Excel (xlsx)."""
    from app.services.analytics.analytics_service import AnalyticsService
    from io import BytesIO
    import pandas as pd
    
    # Parâmetros de período
    start = request.args.get("start")
    end = request.args.get("end")
    if not start or not end:
        today = date.today()
        start = (today - timedelta(days=30)).isoformat()
        end = today.isoformat()
    
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        # KPIs
        kpis = AnalyticsService.get_dashboard_kpis()
        df_kpis = pd.DataFrame([
            {"Métrica": "Chamados Abertos", "Valor": kpis.get("chamados_abertos", 0)},
            {"Métrica": "Chamados do Mês", "Valor": kpis.get("chamados_mes", 0)},
            {"Métrica": "Taxa de SLA (%)", "Valor": kpis.get("sla_taxa", 0)},
            {"Métrica": "Satisfação Média", "Valor": kpis.get("satisfacao_media", 0)},
            {"Métrica": "Lembretes Ativos", "Valor": kpis.get("lembretes_ativos", 0)},
            {"Métrica": "Lembretes Vencidos", "Valor": kpis.get("lembretes_vencidos", 0)},
            {"Métrica": "Equipamentos em Uso", "Valor": kpis.get("equipamentos_uso", 0)},
            {"Métrica": "Total Tutoriais", "Valor": kpis.get("total_tutoriais", 0)},
            {"Métrica": "Visualizações Tutoriais", "Valor": kpis.get("total_visualizacoes", 0)},
            {"Métrica": "Tarefas Concluídas", "Valor": kpis.get("tasks_concluidas", 0)},
            {"Métrica": "Tarefas Pendentes", "Valor": kpis.get("tasks_pendentes", 0)},
        ])
        df_kpis.to_excel(writer, sheet_name="KPIs", index=False)
        
        # Evolução por período
        start_d = date.fromisoformat(start)
        end_d = date.fromisoformat(end)
        evolucao = AnalyticsService.get_chamados_por_periodo(start_d, end_d)
        df_evol = pd.DataFrame(evolucao)
        if not df_evol.empty:
            df_evol.to_excel(writer, sheet_name="Evolucao", index=False)
        
        # Prioridade
        prioridade = AnalyticsService.get_chamados_por_prioridade()
        df_pri = pd.DataFrame(prioridade)
        if not df_pri.empty:
            df_pri.to_excel(writer, sheet_name="Prioridade", index=False)
        
        # Performance técnico
        perf = AnalyticsService.get_performance_por_tecnico(start_d, end_d)
        df_perf = pd.DataFrame(perf)
        if not df_perf.empty:
            df_perf.to_excel(writer, sheet_name="Performance", index=False)
        
        # Setor
        setor = AnalyticsService.get_chamados_por_setor()
        df_set = pd.DataFrame(setor)
        if not df_set.empty:
            df_set.to_excel(writer, sheet_name="Setor", index=False)
    
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"analytics_dashboard_{date.today().isoformat()}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@analytics_bp.route("/api/analytics/export/pdf")
@login_required
def export_pdf():
    """Exporta um PDF com KPIs e tabelas resumidas do dashboard Analytics."""
    from app.services.analytics.analytics_service import AnalyticsService
    from io import BytesIO
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    
    # Parâmetros
    start = request.args.get("start")
    end = request.args.get("end")
    if not start or not end:
        today = date.today()
        start = (today - timedelta(days=30)).isoformat()
        end = today.isoformat()
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)
    
    # Buscar dados
    kpis = AnalyticsService.get_dashboard_kpis()
    evolucao = AnalyticsService.get_chamados_por_periodo(start_d, end_d)
    prioridade = AnalyticsService.get_chamados_por_prioridade()
    perf = AnalyticsService.get_performance_por_tecnico(start_d, end_d)
    setor = AnalyticsService.get_chamados_por_setor()
    
    # Montar PDF
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    content = []
    
    content.append(Paragraph("Dashboard Analytics - Relatório", styles["Title"]))
    content.append(Paragraph(f"Período: {start} a {end}", styles["Normal"]))
    content.append(Spacer(1, 12))
    
    # KPIs
    kpi_table = [["Métrica", "Valor"],
                 ["Chamados Abertos", kpis.get("chamados_abertos", 0)],
                 ["Chamados do Mês", kpis.get("chamados_mes", 0)],
                 ["Taxa de SLA (%)", kpis.get("sla_taxa", 0)],
                 ["Satisfação Média", kpis.get("satisfacao_media", 0)],
                 ["Lembretes Ativos", kpis.get("lembretes_ativos", 0)],
                 ["Lembretes Vencidos", kpis.get("lembretes_vencidos", 0)],
                 ["Equipamentos em Uso", kpis.get("equipamentos_uso", 0)],
                 ["Total Tutoriais", kpis.get("total_tutoriais", 0)],
                 ["Visualizações Tutoriais", kpis.get("total_visualizacoes", 0)],
                 ["Tarefas Concluídas", kpis.get("tasks_concluidas", 0)],
                 ["Tarefas Pendentes", kpis.get("tasks_pendentes", 0)]]
    t = Table(kpi_table, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]))
    content.append(t)
    content.append(Spacer(1, 14))
    
    def add_table(title, data, headers):
        content.append(Paragraph(title, styles['Heading2']))
        rows = [headers] + [list(d.values()) if isinstance(d, dict) else d for d in data]
        tbl = Table(rows, hAlign='LEFT')
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ]))
        content.append(tbl)
        content.append(Spacer(1, 10))
    
    if evolucao:
        add_table("Evolução de Chamados", evolucao, ["periodo", "total"])
    if prioridade:
        add_table("Chamados por Prioridade", prioridade, ["prioridade", "total"])
    if perf:
        add_table("Performance por Técnico", perf, ["tecnico", "total", "tempo_medio", "sla_taxa"])
    if setor:
        add_table("Chamados por Setor", setor, ["setor", "total"])
    
    doc.build(content)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"analytics_dashboard_{date.today().isoformat()}.pdf",
        mimetype='application/pdf'
    )
