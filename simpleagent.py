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
        self.message.append({"parts":[message]})
        return self.execute(self.message)
    def createClient(self):
        genai.configure(api_key=os.environ['GEMINI_API_KEY'])
        return genai.GenerativeModel(model_name='gemini-1.5-flash')    
    def createClient(self):
        genai.configure(api_key=os.environ['GEMINI_API_KEY'])
        return genai.GenerativeModel(model_name='gemini-1.5-flash')
    
    def execute(self, message):
        self.client = self.createClient()
        if message[0].get("parts")[0]:
            return self.client.generate_content(message)


prompt_generate_summary = """
You are a knowledgeable and helpful assistant trained to Provide the Resume readiness according to the prompt.         
Human Message obtained has 2 sections 
        1. Current Resume Data : involving current skills, experience etc.
        2. Job Description (role he is applying for).
Provide clear, concise, and accurate responses that are well-reasoned and evidence-based.Mention the strengths and weakness as per the given job. Also mention the readiness of the candidate for that job.
Strive to understand the context behind each query and address it comprehensively, while remaining respectful and neutral. 
Your goal is to assist user in resume evaluation effectively, ensuring that every answer is informative and reliable.

The output format is expected to be a JSON as :
output:{
        strength :[
        {Relevent Education : },
        {Programming Skills : },
        {Soft Skills :}
        ]
        weakness :[...]
        Area to Improve :[...]
        readiness : "Ready/Almost Ready/Not Ready"
        
        }
}
"""

agent=MyAgent(prompt_generate_summary)
print(agent("Tell me About Tesla X").candidates[0].content.parts[0].text)
