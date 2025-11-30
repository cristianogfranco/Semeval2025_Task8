# Semeval2025_Task8
Tarefa 8 da edição de 2025 do SemEval (Question Answering over Tabular Data)


## Segue uma breve descrição dos arquivos:

### Evaluation.ipynb

Notebook com script para o processamento das avaliações e geração dos resultados. 

### DatabenchDB.py

Classe que representa uma das bases de dados do Databench. Recebe o caminho dos arquivos no formato parquet, o nome da base e o parâmetro indicando a versão (amostra ou
completa) da base de dados. Essa classe cria uma base de dados  SQLITE com base no arquivo parquet, gerencia a conexão com o banco e a execução das consultas SQL.

### MultiAgentsText2SQL.py

Classe que recebe como parâmetros o LLM, a instância do banco de dados DatabenchDB e o tipo de estrutura multiagentes (com ou sem raciocínio). Fica responsável por encapsular a estrutura dos agentes e realizar o processamento das questões e obtenção das respostas. 

### MultiAgentsText2SQL_Tester.py

Classe que apoia na apuração dos resultados, permitindo a execução em batch das questões. 

### Util.py

Arquivo com funções utilitárias. 


# Exemplo de uso das classes 

```python

#Carrega o database

dataset_name = '066_IBM_HR'

execution_mode= DataMode.SAMPLE
databenchDB = DatabenchDB(pathDatasets, pathDatabases, dataset_name, execution_mode)

#Carrega o grafo de agentes
multiAgentsText2SQL= MultiAgentsText2SQL(llm, MultiAgentTypeMode.PLAN_AND_EXECUTE, databenchDB)

multiAgentsText2SQL.Invoke("Are there more employees who travel frequently than those who work in the HR department?")         
