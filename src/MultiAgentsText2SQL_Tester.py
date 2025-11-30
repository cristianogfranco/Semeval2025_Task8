from DatabenchDB import DataMode
class MultiAgentsText2SQL_Tester :

    def __init__(self, multiAgentsText2SQL, datamode):
        
        self.multiAgentsText2SQL = multiAgentsText2SQL
        self.datamode = datamode

    def prompt_generator(self,row: dict) -> str:
        return row["question"]
           
    def call(self, prompts: list[str]) -> list[str]:
        """ Call your model on a batch of prompts here. """
        answers = []
        for prompt in prompts:
            answer = self.multiAgentsText2SQL.Invoke(prompt).replace("'","") #Remove a aspas da resposta
            answer = answer.replace('"',"") #Remove a aspas da resposta
            answer = answer.replace('\n', '').replace('\r', '') #Remove quebra delinha
            answers.append(answer)          

        return answers
