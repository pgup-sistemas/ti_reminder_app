from flask import Blueprint

from .utils.timezone_utils import format_local_datetime, utc_to_local


def register_template_filters(app):
    """Registra filtros personalizados para templates"""

    @app.template_filter("local_datetime")
    def local_datetime_filter(dt, format_str="%d/%m/%Y %H:%M"):
        """Filtro para formatar datetime no timezone local"""
        return format_local_datetime(dt, format_str)

    @app.template_filter("local_date")
    def local_date_filter(dt, format_str="%d/%m/%Y"):
        """Filtro para formatar data no timezone local"""
        return format_local_datetime(dt, format_str)

    @app.template_filter("local_time")
    def local_time_filter(dt, format_str="%H:%M"):
        """Filtro para formatar hora no timezone local"""
        return format_local_datetime(dt, format_str)
