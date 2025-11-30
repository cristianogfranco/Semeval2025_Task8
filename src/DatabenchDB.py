import sqlite3
from enum import Enum, auto
import pandas as pd
import os

class DataMode(Enum):
    """
    Define entre a amostra (20 linhas) ou a base completa com todas as linhas
    """

    SAMPLE = auto()
    ALL = auto()


class DatabenchDB:
    """
    Representa uma das bases de dados do Databench
    """
    def __init__(self, datasets_root_path,database_root_path,dataset_name,mode):
        
        self.datasets_root_path = datasets_root_path
        self.database_root_path = database_root_path
        
        self.dataset_name = dataset_name   

        dataframe = self._ReadParquetDataSet(self.dataset_name, mode)

        table_name = self._ConvertDataSetNameToTableName(self.dataset_name)

        #Nome da base de dados
        db_name = f"db_{self.dataset_name}_{mode.name}.db"
       
        self.db_path = f"{self.database_root_path}/{db_name}"
        
        self._connection = self._ConvertDataFrameToDbConnection(dataframe, table_name)        

    def _ReadParquetDataSet(self,folder_name,mode):    
        """
        Método privado que lê os datasets samples ou all da pasta. 
        :param folder_name: nome da pasta com os arquivos
        :param mode: SAMPLE ou ALL
        :return: dataframe
        """
        
        # Monta os caminhos completos dos arquivos
        if (mode == DataMode.SAMPLE):
            path_dataframe =  self.datasets_root_path + folder_name + '/sample.parquet'
        elif (mode == DataMode.ALL):
            path_dataframe =  self.datasets_root_path + folder_name + '/all.parquet'
        
        # Lê os arquivos parquet para DataFrames
        dataframe= pd.read_parquet(path_dataframe,  engine='fastparquet')
        
        return dataframe

    def _ConvertDataFrameToDbConnection(self,dataframe,table_name):
        """
        Método privado que converte um DataFrame para a conexão do banco de dados criado.
        :param dataframe: dataframe de origem dos dados
        :param table_name: nome da tabela no banco
        :return: conexão ou objeto relacionado
        """
        conn_file = sqlite3.connect(self.DbPath)
        dataframe.to_sql(table_name, conn_file, index=False, if_exists='replace')
        
        return conn_file

    def _ConvertDataSetNameToTableName(self,dataSet_name):
        """
        Método privado que converte o dataset_name para um nome de tabela válido no banco.
        :return: string com nome da tabela
        """
        primVez = True
        table_name = ""
        
        for partName in dataSet_name.split("_"):
            if (primVez):
                primVez = False
            else:
                table_name = table_name + partName
            
        return table_name
    
    def ExecuteQuery(self,Sql):
        """
        Executa uma consulta SQL e retorna um dataframe.
        :param Sql: string com a consulta SQL
        :return: dataframe com os resultados da consulta
        """
        return pd.read_sql_query(Sql, self._connection)

    @property       
    def Close(self):
        """
        Fecha a conexão aberta.
        """
        # Exemplo: fechar conexão se existir
        if self._connection is not None:
            self._connection.close()  # descomente quando implementar conexão real
            self._connection = None
    
                   
    @property
    def Connection(self):
        """
        Retorna a conexão aberta.
        """
        return self._connection

    @property
    def DbPath(self):
        """
        Retorna o path do banco de dados criado.
        """
        return self.db_path

    
   