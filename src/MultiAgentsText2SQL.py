from openai import AzureOpenAI
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing_extensions import TypedDict
from langchain_community.utilities import SQLDatabase
from typing_extensions import Annotated
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langgraph.graph import START, StateGraph
import operator
from typing import Annotated, List, Tuple
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from typing import Union
from typing import Literal
from langgraph.graph import END
from enum import Enum, auto
from typing import Union
from langchain_classic.agents import create_sql_agent
from langchain_classic.agents.agent_toolkits import SQLDatabaseToolkit
from langchain_classic.sql_database import SQLDatabase

from langchain_classic.agents.agent_types import AgentType

from langchain_classic.agents import AgentExecutor, initialize_agent
from langchain_classic.agents import load_tools

class MultiAgentTypeMode(Enum):
    """
    Define o tipo de estrutura de agentes Simples ou com planejamento e execução
    """

    SIMPLE = auto()
    PLAN_AND_EXECUTE = auto()


class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str

class QueryOutput(TypedDict):
    """Generated SQL query."""

    query: Annotated[str, ..., "Syntactically valid SQL query."]


class MultiAgentsText2SQL:
    
    def __init__(self, llm, mode, databenchDB):
        """
        Método de inicialização 
        :param llm: define o LLM usado
        :param mode: define a estrutura de multi-agentes a ser utilizada (Simples ou com Planejamento e Execução) 
        :param databenchDB: a base de dados utilizada
        """

        self.llm = llm
        self.mode = mode
        self.databenchDB = databenchDB
        
        self.system_message = """
        Given an input question, create a syntactically correct {dialect} query to
        run to help find the answer. Unless the user specifies in his question a
        specific number of examples they wish to obtain, always limit your query to
        at most {top_k} results. You can order the results by a relevant column to
        return the most interesting examples in the database.
        
        Never query for all the columns from a specific table, only ask for a the
        few relevant columns given the question.
        
        Pay attention to use only the column names that you can see in the schema
        description. Be careful to not query for columns that do not exist. Also,
        pay attention to which column is in which table.
        
        Only use the following tables:
        {table_info}
        """
        
        self.user_prompt = "Question: {input}"
    
        self.query_prompt_template = ChatPromptTemplate(
            [("system", self.system_message), ("user", self.user_prompt)]
        )
              
        #for message in self.query_prompt_template.messages:
        #    message.pretty_print()   
    
    def Invoke(self, question):
        """
        Executa a chamada ao grafo de agentes informando no prompt a questão a ser respondida.
        :question: questão a ser respondida
        :return: resposta da questão
        """

        answer = ""
        for step in self.Graph.stream({"question": question}, stream_mode="updates"):
            print(step)
            if "GenerateAnswer" in step:
                answer = step["GenerateAnswer"]["answer"]
            
        return answer
           
    @property
    def DbConnection(self):
        """
        Retorna a conexão com tipo compatível SQLDatabase
        """
        return SQLDatabase.from_uri(f"sqlite:///{self.databenchDB.DbPath}")

    def _PlanAndExecuteGraph(self):
       
        def ReactDB_Agent(state: State):
            
            toolkit = SQLDatabaseToolkit(db=self.DbConnection,llm=self.llm)

            tools = SQLDatabaseToolkit(db=self.DbConnection,llm=self.llm).get_tools()

           # Cria uma agente REACT
            db_agent = create_sql_agent(llm=self.llm, toolkit=toolkit, handle_parsing_errors=True, verbose=True, agent_type = AgentType.ZERO_SHOT_REACT_DESCRIPTION)

            try:
                result = db_agent.invoke(state["question"])
            except Exception as e:
                result = "Error"
              
            return  {"result": result}
            
        def GenerateAnswer(state: State):
            """Answer question using retrieved information as context."""
            prompt = (
                """Given the following user question and SQL result, answer the user question.\n\n
                """   
                f"Question: {state['question']}\n"
                f"SQL Result: {state['result']}"            
                """
                Your answer must be of one of these types:

                Boolean: Valid answers include True/False, Y/N, Yes/No (all case insensitive).\n
                Category: A value from a cell (or a substring of a cell) in the dataset.\n
                Number: A numerical value from a cell in the dataset, which may represent a computed statistic (e.g., average, maximum, minimum).\n
                List[category]: A list containing a fixed number of categories. The expected format is: "['cat', 'dog']". Pay attention to the wording of the question to determine if uniqueness is required or if repeated values are allowed.\n
                List[number]: Similar to List[category], but with numbers as its elements.\n

                You don't need to justify your answer or argue.
                You must not include the type in the response, for example List[category].
                
                """
            )
            response = self.llm.invoke(prompt)
            return {"answer": response.content}
                
        
        #Orquestrando com LangGraph 
        graph_builder = StateGraph(State).add_sequence(
            [ReactDB_Agent, GenerateAnswer]
        )
        
        graph_builder.add_edge(START, "ReactDB_Agent")
        
        return graph_builder.compile()

    #Estrutura agentes Simples
    def _SimpleGraph(self):
        """
        Retorna a instância para o Grafo de agentes
        """
        
        def WriteQuery(state: State):
            """Generate SQL query to fetch information."""
            prompt = self.query_prompt_template.invoke(
                {
                    "dialect": self.DbConnection.dialect,
                    "top_k": 10,
                    "table_info": self.DbConnection.get_table_info(),
                    "input": state["question"],
                }
            )
            structured_llm = self.llm.with_structured_output(QueryOutput)
            result = structured_llm.invoke(prompt)
            return {"query": result["query"]}

        def ExecuteQuery(state: State):
            """Execute SQL query."""
            execute_query_tool = QuerySQLDatabaseTool(db=self.DbConnection)
            return {"result": execute_query_tool.invoke(state["query"])}
        
        def GenerateAnswer(state: State):
            """Answer question using retrieved information as context."""
            prompt = (
                """Given the following user question, corresponding SQL query, 
                   and SQL result, answer the user question.\n\n
                """   
                f"Question: {state['question']}\n"
                f"SQL Query: {state['query']}\n"
                f"SQL Result: {state['result']}"
            
                """
                Your answer must be of one of these types:

                Boolean: Valid answers include True/False, Y/N, Yes/No (all case insensitive).\n
                Category: A value from a cell (or a substring of a cell) in the dataset.\n
                Number: A numerical value from a cell in the dataset, which may represent a computed statistic (e.g., average, maximum, minimum).\n
                List[category]: A list containing a fixed number of categories. The expected format is: "['cat', 'dog']". Pay attention to the wording of the question to determine if uniqueness is required or if repeated values are allowed.\n
                List[number]: Similar to List[category], but with numbers as its elements.\n

                You don't need to justify your answer or argue.
                You must not include the type in the response, for example List[category].
                
                """
            )
            response = self.llm.invoke(prompt)
            return {"answer": response.content}
                
        
        #Orquestrando com LangGraph 
        graph_builder = StateGraph(State).add_sequence(
            [WriteQuery, ExecuteQuery, GenerateAnswer]
        )
        
        graph_builder.add_edge(START, "WriteQuery")
        
        return graph_builder.compile()

    @property
    def Graph(self):
        if (self.mode == MultiAgentTypeMode.SIMPLE):
            self.graph = self._SimpleGraph()
        elif (self.mode == MultiAgentTypeMode.PLAN_AND_EXECUTE):
            self.graph = self._PlanAndExecuteGraph()

        return self.graph

        