import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class MyAgent:
    def __init__(self,system_prompt):
        self.system_prompt = system_prompt
        self.message=[] 
    
    def __call__(self,message): 
        if (not message or message.strip() == ""):
            raise ValueError("Message cannot be empty")
        formatted_messages = [
            {"role": "user", "parts": [{"text": message}]},
            {"role": "model", "parts": [{"text": f"System instruction: {self.system_prompt}"}]}
        ]

        return self.execute(formatted_messages)

    def createClient(self):
        genai.configure(api_key=os.environ['GEMINI_API_KEY'])
        return genai.GenerativeModel(model_name='gemini-1.5-flash')
    
    def execute(self, message):
        self.client = self.createClient()
        if message[0].get("parts")[0]:
            return self.client.generate_content(message)
    

def read_transcript(file_path)->str:
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


system_prompt="You are a knowledgeable and helpful assistant trained to answer any kind of question. Provide clear, concise, and accurate responses that are well-reasoned and evidence-based.Strive to understand the context behind each query and address it comprehensively, while remaining respectful and neutral.Your goal is to assist users effectively, ensuring that every answer is informative and reliable."

agent=MyAgent(system_prompt)
transcript=read_transcript('transcript.txt')
print(agent(transcript).candidates[0].content.parts[0].text)