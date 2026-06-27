import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# pegando a pasta certa pra não dar erro no caminho do banco
diretorio_script = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(diretorio_script) == 'scripts':
    raiz_projeto = os.path.dirname(diretorio_script)
else:
    raiz_projeto = diretorio_script

caminho_db = os.path.join(raiz_projeto, 'data', 'processed', 'acidentes_transito.duckdb')

print("conectando no banco...")
con = duckdb.connect(caminho_db)

sns.set_theme(style="whitegrid")


# grafico 1: ruas com mais acidentes

print("fazendo o grafico das piores ruas...")

# query para agrupar o pessoal por boletim e depois cruzar com as ruas
df_vias = con.execute("""
    with pessoas_boletim as (
        select 
            numero_boletim,
            count(num_envolvido) as qtd_pessoas_total,
            -- severidade 2 significa obito no dicionario de dados
            sum(case when cod_severidade = 2 then 1 else 0 end) as qtd_vitimas_fatais
        from ENVOLVIDOS
        group by numero_boletim
    ),
    vias as (
        select 
            l.nome_logradouro,
            count(distinct b.numero_boletim) as total_acidentes,
            sum(p.qtd_pessoas_total) as total_pessoas_envolvidas,
            sum(p.qtd_vitimas_fatais) as total_vitimas_fatais
        from BOLETINS b
        join BOLETIM_LOGRADOUROS bl on b.numero_boletim = bl.numero_boletim
        join LOGRADOURO l on bl.num_logradouro = l.num_logradouro
        left join pessoas_boletim p on b.numero_boletim = p.numero_boletim
        where l.nome_logradouro is not null 
        group by l.nome_logradouro
    )
    -- calculando a porcentagem final
    select 
        nome_logradouro,
        total_acidentes,
        total_pessoas_envolvidas,
        total_vitimas_fatais,
        round((total_vitimas_fatais * 100.0 / nullif(total_pessoas_envolvidas, 0)), 2) as taxa_letalidade_pct
    from vias
    where total_acidentes >= 50 
    order by total_acidentes desc
    limit 10;
""").df()

fig1, ax1 = plt.subplots(figsize=(12, 6))
sns.barplot(data=df_vias, x='total_acidentes', y='nome_logradouro', color='steelblue', ax=ax1)
ax1.set_xlabel('Total de Acidentes', fontsize=12)
ax1.set_ylabel('Logradouro', fontsize=12)
ax1.set_title('Top 10 Vias com Mais Acidentes e Letalidade (Por Pessoas Envolvidas)', fontsize=14, fontweight='bold')

# bota os textos com a porcentagem do lado de cada barra
for index, row in df_vias.iterrows():
    texto = f"{row['taxa_letalidade_pct']}% letalidade ({row['total_vitimas_fatais']} óbitos)"
    ax1.text(row['total_acidentes'] + 5, index, texto, color='red', va='center')

plt.tight_layout()
plt.show()



# grafico 2: quem são os motoristas (idade/sexo)

print("gerando grafico de pizza do perfil dos motoristas...")

df_perfil = con.execute("""
    select 
        sexo,
        count(distinct numero_boletim || num_envolvido) as total_condutores_envolvidos,
        round(avg(idade), 1) as idade_media
    from ENVOLVIDOS
    where condutor = 'S' 
      and idade is not null 
      and idade between 16 and 95 
      and sexo in ('M', 'F') 
    group by sexo
    having count(distinct numero_boletim || num_envolvido) > 1000 
    order by total_condutores_envolvidos desc;
""").df()

fig2, ax2 = plt.subplots(figsize=(8, 8))
cores = ['#3498db', '#e74c3c'] # azul = M, vermelho = F
ax2.pie(df_perfil['total_condutores_envolvidos'], labels=df_perfil['sexo'], autopct='%1.1f%%', 
        startangle=90, colors=cores, textprops={'fontsize': 12})
ax2.set_title('Proporção de Condutores Envolvidos em Acidentes por Sexo\n(e Idade Média)', fontsize=14, fontweight='bold')

# arrumando a legenda pra colocar a idade media junto
legenda = [f"Sexo {row['sexo']}: Média de {row['idade_media']} anos" for index, row in df_perfil.iterrows()]
ax2.legend(legenda, loc="best")

plt.tight_layout()
plt.show()


# grafico 3: horas do dia x mortes

print("ultimo grafico: olhando os horarios...")

df_hora = con.execute("""
    with horas as (
        select 
            cast(extract(hour from b.data_hora_boletim) as integer) as hora_dia,
            count(e.num_envolvido) as total_pessoas,
            sum(case when e.cod_severidade = 2 then 1 else 0 end) as obitos
        from BOLETINS b
        join ENVOLVIDOS e on b.numero_boletim = e.numero_boletim
        where b.data_hora_boletim is not null
        group by extract(hour from b.data_hora_boletim)
    )
    select 
        hora_dia,
        total_pessoas,
        obitos,
        -- multiplicando por mil em vez de 100 pra linha ficar melhor no grafico
        round((obitos * 1000.0 / nullif(total_pessoas, 0)), 2) as letalidade_por_mil
    from horas
    order by hora_dia;
""").df()

# criando o grafico com dois eixos (barras e linha)
fig3, ax_bar = plt.subplots(figsize=(12, 6))

# primeiro eixo: barras azuis pro total de pessoas
sns.barplot(data=df_hora, x='hora_dia', y='total_pessoas', color='#3498db', ax=ax_bar, alpha=0.7)
ax_bar.set_xlabel('Hora do Dia (00h - 23h)', fontsize=12, fontweight='bold')
ax_bar.set_ylabel('Total de Pessoas Envolvidas', fontsize=12, color='#2980b9', fontweight='bold')
ax_bar.tick_params(axis='y', labelcolor='#2980b9')

# segundo eixo: linha vermelha pra taxa de letalidade
ax_linha = ax_bar.twinx()
# o df_hora.index serve pra centralizar as bolinhas da linha com o meio das barras
sns.lineplot(data=df_hora, x=df_hora.index, y='letalidade_por_mil', color='#e74c3c', ax=ax_linha, marker='o', linewidth=2.5, markersize=8)
ax_linha.set_ylabel('Taxa de Letalidade (Óbitos a cada 1.000 pessoas)', fontsize=12, color='#c0392b', fontweight='bold')
ax_linha.tick_params(axis='y', labelcolor='#c0392b')
ax_linha.grid(False) 

plt.title('Paradoxo do Trânsito: Horário de Pico vs. Madrugada', fontsize=15, fontweight='bold')
plt.tight_layout()
plt.show()

print("tudo pronto, fechando o banco!")
con.close()