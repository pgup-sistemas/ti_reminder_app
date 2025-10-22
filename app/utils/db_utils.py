"""
Utilitários centralizados para operações de banco de dados.
Consolida toda lógica de conexão e operações diretas ao banco.
"""
import os
from urllib.parse import urlparse
from contextlib import contextmanager
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text, inspect
from flask import current_app


class DatabaseManager:
    """Gerenciador centralizado de operações de banco de dados."""
    
    @staticmethod
    def get_database_url() -> str:
        """
        Obtém a URL do banco de dados de forma consistente.
        
        Returns:
            str: URL do banco de dados
            
        Raises:
            ValueError: Se DATABASE_URL não estiver configurada
        """
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            raise ValueError(
                "DATABASE_URL não configurada. "
                "Configure no arquivo .env: DATABASE_URL=postgresql://user:pass@host:port/dbname"
            )
        
        # Garantir que é PostgreSQL
        if not database_url.startswith('postgresql'):
            raise ValueError(
                "Apenas PostgreSQL é suportado. "
                "DATABASE_URL deve começar com 'postgresql://'"
            )
        
        return database_url
    
    @staticmethod
    def parse_database_url(database_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Parseia a URL do banco de dados em componentes.
        
        Args:
            database_url: URL do banco (opcional, usa env se não fornecida)
            
        Returns:
            Dict com dbname, user, password, host, port
        """
        if not database_url:
            database_url = DatabaseManager.get_database_url()
        
        url = urlparse(database_url)
        
        return {
            'dbname': url.path[1:] if url.path else '',
            'user': url.username,
            'password': url.password,
            'host': url.hostname,
            'port': url.port or 5432
        }
    
    @staticmethod
    @contextmanager
    def get_raw_connection(database_url: Optional[str] = None, autocommit: bool = False):
        """
        Context manager para conexão psycopg2 direta.
        
        Args:
            database_url: URL do banco (opcional)
            autocommit: Se True, ativa autocommit
            
        Yields:
            Tupla (connection, cursor)
            
        Example:
            with DatabaseManager.get_raw_connection() as (conn, cursor):
                cursor.execute("SELECT * FROM user")
                results = cursor.fetchall()
        """
        conn = None
        cursor = None
        
        try:
            params = DatabaseManager.parse_database_url(database_url)
            conn = psycopg2.connect(**params)
            
            if autocommit:
                conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            yield conn, cursor
            
            if not autocommit:
                conn.commit()
                
        except Exception as e:
            if conn and not autocommit:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    @staticmethod
    def database_exists(dbname: str, database_url: Optional[str] = None) -> bool:
        """
        Verifica se um banco de dados existe.
        
        Args:
            dbname: Nome do banco de dados
            database_url: URL base (conecta ao postgres)
            
        Returns:
            bool: True se o banco existe
        """
        try:
            params = DatabaseManager.parse_database_url(database_url)
            params['dbname'] = 'postgres'  # Conecta ao banco padrão
            
            with DatabaseManager.get_raw_connection(autocommit=True) as (conn, cursor):
                cursor.execute(
                    "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                    (dbname,)
                )
                return cursor.fetchone() is not None
        except Exception:
            return False
    
    @staticmethod
    def create_database(dbname: str, database_url: Optional[str] = None) -> bool:
        """
        Cria um banco de dados se não existir.
        
        Args:
            dbname: Nome do banco de dados
            database_url: URL base
            
        Returns:
            bool: True se criado ou já existe
        """
        try:
            if DatabaseManager.database_exists(dbname, database_url):
                # Banco de dados já existe
                return True
            
            params = DatabaseManager.parse_database_url(database_url)
            params['dbname'] = 'postgres'
            
            conn = psycopg2.connect(**params)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            cursor.execute(f'CREATE DATABASE "{dbname}"')
            # Banco de dados criado com sucesso
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            # Erro ao criar banco de dados
            return False
    
    @staticmethod
    def column_exists(table_name: str, column_name: str) -> bool:
        """
        Verifica se uma coluna existe em uma tabela.
        
        Args:
            table_name: Nome da tabela
            column_name: Nome da coluna
            
        Returns:
            bool: True se a coluna existe
        """
        try:
            with DatabaseManager.get_raw_connection() as (conn, cursor):
                cursor.execute("""
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND column_name = %s
                """, (table_name, column_name))
                return cursor.fetchone() is not None
        except Exception:
            return False
    
    @staticmethod
    def table_exists(table_name: str) -> bool:
        """
        Verifica se uma tabela existe.
        
        Args:
            table_name: Nome da tabela
            
        Returns:
            bool: True se a tabela existe
        """
        try:
            with DatabaseManager.get_raw_connection() as (conn, cursor):
                cursor.execute("""
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_name = %s
                """, (table_name,))
                return cursor.fetchone() is not None
        except Exception:
            return False
    
    @staticmethod
    def get_table_columns(table_name: str) -> list:
        """
        Obtém lista de colunas de uma tabela.
        
        Args:
            table_name: Nome da tabela
            
        Returns:
            Lista de nomes de colunas
        """
        try:
            with DatabaseManager.get_raw_connection() as (conn, cursor):
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                return [row[0] for row in cursor.fetchall()]
        except Exception:
            return []
    
    @staticmethod
    def test_connection(verbose: bool = True) -> bool:
        """
        Testa a conexão com o banco de dados.
        
        Args:
            verbose: Se True, imprime informações detalhadas
            
        Returns:
            bool: True se a conexão foi bem-sucedida
        """
        try:
            database_url = DatabaseManager.get_database_url()
            params = DatabaseManager.parse_database_url(database_url)
            
            if verbose:
                # Testando conexão com o banco de dados
                pass
                
            with DatabaseManager.get_raw_connection() as (conn, cursor):
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                
                if verbose:
                    # Conexão estabelecida com sucesso
                    
                    # Listar tabelas
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """)
                    table_count = cursor.fetchone()[0]
                    # Tabelas no banco contabilizadas
                
                return True
                
        except Exception as e:
            if verbose:
                # Erro ao conectar ao banco de dados
                pass
            return False


class MigrationHelper:
    """Helper para operações relacionadas a migrações."""
    
    @staticmethod
    def add_column_if_not_exists(
        table_name: str,
        column_name: str,
        column_type: str,
        nullable: bool = True,
        default: Optional[str] = None
    ) -> bool:
        """
        Adiciona uma coluna se ela não existir.
        
        Args:
            table_name: Nome da tabela
            column_name: Nome da coluna
            column_type: Tipo SQL da coluna
            nullable: Se a coluna aceita NULL
            default: Valor padrão (opcional)
            
        Returns:
            bool: True se adicionada ou já existe
        """
        try:
            if DatabaseManager.column_exists(table_name, column_name):
                # Coluna já existe na tabela
                return True
            
            with DatabaseManager.get_raw_connection() as (conn, cursor):
                sql = f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {column_type}'
                
                if not nullable:
                    sql += ' NOT NULL'
                
                if default is not None:
                    sql += f' DEFAULT {default}'
                
                cursor.execute(sql)
                # Coluna adicionada com sucesso
                return True
                
        except Exception as e:
            # Erro ao adicionar coluna
            return False
