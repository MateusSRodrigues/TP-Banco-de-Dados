import duckdb
import os

# pegando a pasta certa pra rodar o script sem dar erro de caminho
diretorio_script = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(diretorio_script) == 'scripts':
    raiz_projeto = os.path.dirname(diretorio_script)
else:
    raiz_projeto = diretorio_script

caminho_db = os.path.join(raiz_projeto, 'data', 'processed', 'acidentes_transito.duckdb')
caminho_raw = os.path.join(raiz_projeto, 'data', 'raw')

print(f"pasta do projeto: {raiz_projeto}")
print("começando a criar o banco de dados...")

con = duckdb.connect(caminho_db)

# recriando as tabelas do zero
print("apagando tabelas antigas e criando as novas...")
con.execute("""
    -- apagando as tabelas de acidentes primeiro por causa das chaves estrangeiras
    drop table if exists ENVOLVIDOS;
    drop table if exists VEICULOS;
    drop table if exists BOLETIM_LOGRADOUROS;
    drop table if exists BOLETINS;

    -- apagando as tabelas de categorias/dominios
    drop table if exists LOGRADOURO;
    drop table if exists BAIRRO;
    drop table if exists TIPO_ACIDENTE;
    drop table if exists TEMPO;
    drop table if exists PAVIMENTO;
    drop table if exists REGIONAL;
    drop table if exists UPS;
    drop table if exists CATEGORIA_VEICULO;
    drop table if exists ESPECIE_VEICULO;
    drop table if exists SITUACAO_VEICULO;
    drop table if exists TIPO_SOCORRO;
    drop table if exists SEVERIDADE_ENVOLVIDO;
    drop table if exists CATEGORIA_HABILITACAO;

    -- criando as tabelas de categorias 
    create table TIPO_ACIDENTE (
        tipo_acidente varchar primary key,
        desc_tipo_acidente varchar
    );

    create table TEMPO (
        cod_tempo integer primary key,
        desc_tempo varchar
    );

    create table PAVIMENTO (
        cod_pavimento integer primary key,
        desc_pavimento varchar
    );

    create table REGIONAL (
        cod_regional integer primary key,
        desc_regional varchar
    );

    create table UPS (
        valor_ups integer primary key,
        desc_ups varchar
    );

    create table BAIRRO (
        numero_bairro integer primary key,
        nome_bairro varchar
    );

    create table LOGRADOURO (
        num_logradouro integer primary key,
        nome_logradouro varchar,
        tipo_logradouro varchar,
        numero_bairro integer,
        constraint fk_logradouro_bairro foreign key (numero_bairro) references BAIRRO(numero_bairro)
    );

    create table CATEGORIA_VEICULO (
        cod_categ integer primary key,
        desc_categ varchar
    );

    create table ESPECIE_VEICULO (
        cod_especie integer primary key,
        desc_especie varchar
    );

    create table SITUACAO_VEICULO (
        cod_situacao integer primary key,
        desc_situacao varchar
    );

    create table TIPO_SOCORRO (
        tipo_socorro integer primary key,
        desc_socorro varchar
    );

    create table SEVERIDADE_ENVOLVIDO (
        cod_severidade integer primary key,
        desc_severidade varchar
    );

    create table CATEGORIA_HABILITACAO (
        categoria_habilitacao varchar primary key,
        descricao_habilitacao varchar
    );

    -- criando as tabelas principais (boletins, pessoas, etc)
    create table BOLETINS (
        numero_boletim varchar primary key,
        data_hora_boletim timestamp,
        local_sinalizado varchar,
        velocidade_permitida integer,
        coordenada_x decimal(12,2),
        coordenada_y decimal(12,2),
        indicador_fatalidade varchar,
        tipo_acidente varchar,
        cod_tempo integer,
        cod_pavimento integer,
        cod_regional integer,
        valor_ups integer,
        constraint fk_boletins_tipo_acidente foreign key (tipo_acidente) references TIPO_ACIDENTE(tipo_acidente),
        constraint fk_boletins_tempo foreign key (cod_tempo) references TEMPO(cod_tempo),
        constraint fk_boletins_pavimento foreign key (cod_pavimento) references PAVIMENTO(cod_pavimento),
        constraint fk_boletins_regional foreign key (cod_regional) references REGIONAL(cod_regional),
        constraint fk_boletins_ups foreign key (valor_ups) references UPS(valor_ups)
    );

    create table BOLETIM_LOGRADOUROS (
        numero_boletim varchar,
        seq_logradouros integer,
        numero_imovel varchar,
        num_logradouro integer,
        primary key (numero_boletim, seq_logradouros),
        constraint fk_bl_boletim foreign key (numero_boletim) references BOLETINS(numero_boletim),
        constraint fk_bl_logradouro foreign key (num_logradouro) references LOGRADOURO(num_logradouro)
    );

    create table VEICULOS (
        numero_boletim varchar,
        seq_veic integer,
        cod_categ integer,
        cod_especie integer,
        cod_situacao integer,
        tipo_socorro integer,
        primary key (numero_boletim, seq_veic),
        constraint fk_veiculos_boletim foreign key (numero_boletim) references BOLETINS(numero_boletim),
        constraint fk_veiculos_categoria foreign key (cod_categ) references CATEGORIA_VEICULO(cod_categ),
        constraint fk_veiculos_especie foreign key (cod_especie) references ESPECIE_VEICULO(cod_especie),
        constraint fk_veiculos_situacao foreign key (cod_situacao) references SITUACAO_VEICULO(cod_situacao),
        constraint fk_veiculos_socorro foreign key (tipo_socorro) references TIPO_SOCORRO(tipo_socorro)
    );

    create table ENVOLVIDOS (
        numero_boletim varchar,
        num_envolvido integer,
        condutor varchar,
        sexo varchar,
        cinto_seguranca varchar,
        embriaguez varchar,
        idade integer,
        pedestre varchar,
        passageiro varchar,
        cod_severidade integer,
        categoria_habilitacao varchar,
        primary key (numero_boletim, num_envolvido),
        constraint fk_envolvidos_boletim foreign key (numero_boletim) references BOLETINS(numero_boletim),
        constraint fk_envolvidos_severidade foreign key (cod_severidade) references SEVERIDADE_ENVOLVIDO(cod_severidade),
        constraint fk_envolvidos_habilitacao foreign key (categoria_habilitacao) references CATEGORIA_HABILITACAO(categoria_habilitacao)
    );
""")


print("lendo os arquivos csv brutos...")
con.execute(f"""
    -- jogando os csvs pra tabelas temporarias pra organizar os nomes das colunas
    
    -- boletins
    create temp table stg_bol as 
    select 
        numero_boletim,
        coalesce(
            try_strptime(data_hora_boletim, '%d/%m/%Y %H:%M:%S'),
            try_strptime(data_hora_boletim, '%d/%m/%Y %H:%M')
        ) as data_hora_boletim,    
        tipo_acidente, 
        desc_tipo_acidente, 
        cod_tempo, 
        desc_tempo, 
        cod_pavimento, 
        desc_pavimento, 
        local_sinalizado, 
        cod_regional, 
        desc_regional, 
        velocidade_permitida, 
        coordenada_x, 
        coordenada_y, 
        indicador_fatalidade, 
        valor_ups, 
        desc_ups
    from read_csv_auto(
        '{caminho_raw}/si-bol-*.csv', 
        encoding='8859_1',
        ignore_errors=true, 
        header=true, -- pula o cabecalho antigo
        names=[
            'numero_boletim',     
            'data_hora_boletim', 
            'ignorar_1',          
            'tipo_acidente',      
            'desc_tipo_acidente',
            'cod_tempo',
            'desc_tempo',
            'cod_pavimento',
            'desc_pavimento',
            'cod_regional',
            'desc_regional',
            'ignorar_5',
            'local_sinalizado',
            'velocidade_permitida',
            'coordenada_x',
            'coordenada_y',
            'ignorar_6',
            'indicador_fatalidade',
            'valor_ups',
            'desc_ups',
            'ignorar_8',
            'ignorar_9',
            'ignorar_10',
            'ignorar_11'
        ]
    );

    -- ruas
    create temp table stg_log as 
    select numero_boletim, seq_logradouros, num_logradouro, tipo_logradouro, numero_imovel, nome_logradouro, numero_bairro, nome_bairro
    from read_csv_auto(
        '{caminho_raw}/si-log-*.csv', 
        encoding='8859_1',
        ignore_errors=true, 
        header=true,
        names=[
            'numero_boletim', 
            'ignorar_1',
            'ignorar_2',
            'ignorar_3',
            'seq_logradouros', 
            'num_logradouro',
            'tipo_logradouro', 
            'nome_logradouro',
            'ignorar_5',
            'ignorar_6',
            'numero_bairro',
            'nome_bairro',
            'ignorar_7',
            'ignorar_8',
            'numero_imovel', 
            'ignorar_9'
        ]
    );

    -- veiculos
    create temp table stg_veic as
    select numero_boletim, seq_veic, cod_categ, desc_categ, cod_especie, desc_especie, cod_situacao, desc_situacao, tipo_socorro, desc_socorro
    from read_csv_auto(
        '{caminho_raw}/si-veic-*.csv', 
        encoding='8859_1',
        ignore_errors=true, 
        header=true,
        names=[
            'numero_boletim', 
            'ignorar_1',
            'seq_veic', 
            'cod_categ', 
            'desc_categ',
            'cod_especie', 
            'desc_especie',
            'cod_situacao', 
            'desc_situacao',
            'tipo_socorro',
            'desc_socorro'
        ]
    );

    -- pessoas envolvidas
    create temp table stg_env as
    select numero_boletim, num_envolvido, condutor, cod_severidade, desc_severidade, sexo, cinto_seguranca, embriaguez, idade, categoria_habilitacao, desc_habilitacao, especie_veiculo, pedestre, passageiro
    from read_csv_auto(
        '{caminho_raw}/si-env-*.csv', 
        encoding='8859_1',
        ignore_errors=true, 
        header=true,
        names=[
            'numero_boletim', 
            'ignorar_1',
            'num_envolvido', 
            'condutor',
            'cod_severidade', 
            'desc_severidade', 
            'sexo', 
            'cinto_seguranca', 
            'embriaguez', 
            'idade', 
            'ignorar_2',
            'categoria_habilitacao', 
            'desc_habilitacao',
            'ignorar_3',
            'ignorar_4',
            'especie_veiculo',
            'pedestre',
            'passageiro'
        ]
    );
""")

print("preenchendo o banco de dados...")
con.execute("""
    -- preenchendo as tabelas de categorias usando MAX pra nao quebrar se tiver duplicado no csv

    insert into TIPO_ACIDENTE 
    select tipo_acidente, max(desc_tipo_acidente) from stg_bol where tipo_acidente is not null group by tipo_acidente;

    insert into TEMPO 
    select cod_tempo, max(desc_tempo) from stg_bol where cod_tempo is not null group by cod_tempo;

    insert into PAVIMENTO 
    select cod_pavimento, max(desc_pavimento) from stg_bol where cod_pavimento is not null group by cod_pavimento;

    insert into REGIONAL 
    select cod_regional, max(desc_regional) from stg_bol where cod_regional is not null group by cod_regional;

    insert into UPS 
    select valor_ups, max(desc_ups) from stg_bol where valor_ups is not null group by valor_ups;

    insert into BAIRRO 
    select numero_bairro, max(nome_bairro) from stg_log where numero_bairro is not null group by numero_bairro;

    insert into LOGRADOURO 
    select num_logradouro, max(nome_logradouro), max(tipo_logradouro), max(numero_bairro) 
    from stg_log where num_logradouro is not null group by num_logradouro;

    insert into CATEGORIA_VEICULO 
    select cod_categ, max(desc_categ) from stg_veic where cod_categ is not null group by cod_categ;

    insert into ESPECIE_VEICULO 
    select cod_especie, max(desc_especie) from stg_veic where cod_especie is not null group by cod_especie;

    insert into SITUACAO_VEICULO 
    select cod_situacao, max(desc_situacao) from stg_veic where cod_situacao is not null group by cod_situacao;

    insert into TIPO_SOCORRO 
    select tipo_socorro, max(desc_socorro) from stg_veic where tipo_socorro is not null group by tipo_socorro;

    insert into SEVERIDADE_ENVOLVIDO 
    select cod_severidade, max(desc_severidade) from stg_env where cod_severidade is not null group by cod_severidade;

    insert into CATEGORIA_HABILITACAO 
    select categoria_habilitacao, max(desc_habilitacao) from stg_env where categoria_habilitacao is not null group by categoria_habilitacao;


    -- agora preenchendo as tabelas principais de acidentes
    -- on conflict do nothing vai pular a linha caso o boletim ja exista no banco

    insert into BOLETINS
    select distinct numero_boletim, data_hora_boletim, local_sinalizado, velocidade_permitida, coordenada_x, coordenada_y, indicador_fatalidade, tipo_acidente, cod_tempo, cod_pavimento, cod_regional, valor_ups
    from stg_bol
    where numero_boletim is not null
    on conflict (numero_boletim) do nothing;

    insert into BOLETIM_LOGRADOUROS
    select distinct numero_boletim, seq_logradouros, numero_imovel, num_logradouro
    from stg_log
    where numero_boletim is not null and seq_logradouros is not null
      -- garante que o boletim principal ja foi cadastrado
      and numero_boletim in (select numero_boletim from BOLETINS)
    on conflict (numero_boletim, seq_logradouros) do nothing;

    insert into VEICULOS
    select distinct numero_boletim, seq_veic, cod_categ, cod_especie, cod_situacao, tipo_socorro
    from stg_veic
    where numero_boletim is not null and seq_veic is not null
      and numero_boletim in (select numero_boletim from BOLETINS)
    on conflict (numero_boletim, seq_veic) do nothing;

    insert into ENVOLVIDOS
    select distinct numero_boletim, num_envolvido, condutor, sexo, cinto_seguranca, embriaguez, idade, pedestre, passageiro, cod_severidade, categoria_habilitacao
    from stg_env
    where numero_boletim is not null and num_envolvido is not null
      and numero_boletim in (select numero_boletim from BOLETINS)
    on conflict (numero_boletim, num_envolvido) do nothing;
""")

con.close()
print("pronto! banco de dados criado e atualizado com sucesso na pasta processed.")