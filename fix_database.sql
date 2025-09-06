-- Ajusta o tamanho da coluna password_hash para 255 caracteres
ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(255);

-- Adiciona as colunas de SLA que estão faltando na tabela chamado
ALTER TABLE chamado 
    ADD COLUMN IF NOT EXISTS prazo_sla TIMESTAMP,
    ADD COLUMN IF NOT EXISTS data_primeira_resposta TIMESTAMP,
    ADD COLUMN IF NOT EXISTS sla_cumprido BOOLEAN,
    ADD COLUMN IF NOT EXISTS tempo_resposta_horas FLOAT;

-- Cria a tabela sla_config se não existir
CREATE TABLE IF NOT EXISTS sla_config (
    id SERIAL PRIMARY KEY,
    prioridade VARCHAR(50) NOT NULL UNIQUE,
    tempo_resposta_horas INTEGER NOT NULL,
    tempo_resolucao_horas INTEGER,
    ativo BOOLEAN DEFAULT TRUE
);

-- Insere configurações padrão de SLA se a tabela estiver vazia
INSERT INTO sla_config (prioridade, tempo_resposta_horas, tempo_resolucao_horas, ativo)
SELECT 'Baixa', 48, 168, TRUE
WHERE NOT EXISTS (SELECT 1 FROM sla_config WHERE prioridade = 'Baixa');

INSERT INTO sla_config (prioridade, tempo_resposta_horas, tempo_resolucao_horas, ativo)
SELECT 'Media', 24, 72, TRUE
WHERE NOT EXISTS (SELECT 1 FROM sla_config WHERE prioridade = 'Media');

INSERT INTO sla_config (prioridade, tempo_resposta_horas, tempo_resolucao_horas, ativo)
SELECT 'Alta', 4, 24, TRUE
WHERE NOT EXISTS (SELECT 1 FROM sla_config WHERE prioridade = 'Alta');

-- Atualiza a tabela de migração para refletir as alterações
-- Isso evita que o Alembic tente aplicar as migrações novamente
INSERT INTO alembic_version (version_num)
SELECT 'b91b0d7d62b4'
WHERE NOT EXISTS (SELECT 1 FROM alembic_version WHERE version_num = 'b91b0d7d62b4');
