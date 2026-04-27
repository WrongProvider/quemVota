-- Ordem importa: tabelas pai primeiro

-- 1. Legislatura (necessária para Deputado)
INSERT INTO legislaturas (id, "idLegislatura", "dataInicio", "dataFim", "anoEleicao")
VALUES (1, 57, '2023-02-01', '2027-01-31', 2022);

-- 2. Partido (necessário para Deputado)
INSERT INTO partidos (id, "idCamara", nome, sigla, "numeroEleitoral", situacao)
VALUES (1, 36769, 'Partido Teste', 'PT', 13, 'Ativo');

-- 3. Deputados (os dois que os testes vão usar)
INSERT INTO deputados (id, "idCamara", nome, slug, "siglaUF", "siglaPartido", "idPartido", situacao)
VALUES
  (1, 204554, 'Fulano Silva', 'fulano-silva', 'SP', 'PT', 1, 'Exercício'),
  (2, 204555, 'Ciclana Souza', 'ciclana-souza', 'RJ', 'PT', 1, 'Exercício');

INSERT INTO votacoes
