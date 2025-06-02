-- Script para adicionar a coluna sector_id à tabela user
-- Execute este script no seu banco de dados SQLite

-- Primeiro, verifique se a coluna já existe
SELECT COUNT(*) AS column_exists 
FROM pragma_table_info('user') 
WHERE name = 'sector_id';

-- Se a coluna não existir (resultado = 0), execute o ALTER TABLE
-- Descomente a linha abaixo para executar a alteração
-- ALTER TABLE user ADD COLUMN sector_id INTEGER REFERENCES sector(id) ON DELETE SET NULL;

-- Para verificar se a coluna foi adicionada com sucesso
-- SELECT * FROM pragma_table_info('user') WHERE name = 'sector_id';
