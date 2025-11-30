import os
import glob
import os
import re
import pandas as pd

#Salva uma lista como um arquivo
def SaveList2File(lst, file_path):
    """
    Saves elements of a list to a text file, one element per line.
    :param lst: list of elements (will be converted to string)
    :param file_path: path where the file will be saved
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in lst:
            f.write(str(item) + '\n')
            
#Cria diretório          
def CreateDirectory(path):
    """
    Creates a directory at the specified path, including parent directories if needed.
    :param path: path of the directory to be created
    """
    os.makedirs(path, exist_ok=True)



#Cria um relatorio de analise com o consolidado de todas as questões, respostas de referencia, comparadas com as 
#respostas do modelo e avaliaçõa para as bases SAMPLE e FULL
def CreateAnalysisReport(pathResults):

    pathResults = pathResults.rstrip('/')
    
    # Retorna o nome da pasta com resultado dos testes. 
    # Este nome tb compóe o nome dos arquivos
    timestamp_folder_result_name =  pathResults.split('/')[-1]

    padrao = os.path.join(pathResults, f"qa_*_ALL_{timestamp_folder_result_name}.csv")
    qa_files = glob.glob(padrao)

    first_time = True
    
    for qa_file in qa_files:        
        
        #Resgata o nome do dataSet
        padrao = rf'qa_(.+)_ALL_{timestamp_folder_result_name}\.csv'
        result = re.search(padrao, qa_file)
        dataset_name = result.group(1)

        #Carrega o dataframe com as Quesions and Answers        
        df_qa = pd.read_csv(qa_file)

        ## Lê as respostas do modelo para a base SAMPLE
        model_sample_answer_file_name = f"model_responses_{dataset_name}_SAMPLE_{timestamp_folder_result_name}.txt"
        with open(f"{pathResults}/{model_sample_answer_file_name}", 'r') as f:
            values = [line.strip() for line in f]
        
        df_qa['model_sample_answer'] = values

        ## Lê as respostas do modelo para a base ALL
        model_all_answer_file_name = f"model_responses_{dataset_name}_ALL_{timestamp_folder_result_name}.txt"
        with open(f"{pathResults}/{model_all_answer_file_name}", 'r') as f:
            values = [line.strip() for line in f]
        
        df_qa['model_all_answer'] = values
        
        ## Lê as avaliações do modelo para a base SAMPLE
        eval_sample_file_name = f"eval_{dataset_name}_SAMPLE_{timestamp_folder_result_name}.txt"
        with open(f"{pathResults}/{eval_sample_file_name}", 'r') as f:
            values = [line.strip() for line in f]

        df_qa['eval_sample'] = values

        ## Lê as avaliações do modelo para a base ALL
        eval_all_file_name = f"eval_{dataset_name}_ALL_{timestamp_folder_result_name}.txt"
        with open(f"{pathResults}/{eval_all_file_name}", 'r') as f:
            values = [line.strip() for line in f]

        df_qa['eval_all'] = values

        # Concatenar os DataFrames de todas as bases
        if (first_time):   
            df_analysis = df_qa
            first_time = False
        else:
            df_analysis = pd.concat([df_analysis, df_qa], ignore_index=True)

        # Salvar como arquivo CSV o relatorio consolidado com as respostas e avaliações dos modelos
        df_analysis.to_csv(f"{pathResults}/relatorio_analise_{timestamp_folder_result_name}.csv", index=False) 