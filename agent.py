import os
from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()


class MyAgent:
    def __init__(self, system_prompt: str, *, model: str | None = None):
        self.system_prompt = system_prompt
        self.model = model or os.getenv("MISTRAL_MODEL", "mistral-large-latest")
        self._client = None

    @property
    def client(self) -> Mistral:
        if self._client is None:
            api_key = os.getenv("MISTRAL_API_KEY")
            if not api_key:
                raise RuntimeError("MISTRAL_API_KEY is not set in the environment")
            self._client = Mistral(api_key=api_key)
        return self._client

    def __call__(self, message: str):
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        response = self.client.chat.complete(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message},
            ],
        )

        if not response.choices:
            raise RuntimeError("Mistral response did not include any choices")

        return response.choices[0].message.content.strip()


def read_transcript(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


system_prompt = (
    "You are a knowledgeable and helpful assistant trained to answer any kind of "
    "question. Provide clear, concise, and accurate responses that are well-reasoned "
    "and evidence-based. Strive to understand the context behind each query and address "
    "it comprehensively, while remaining respectful and neutral. Your goal is to assist "
    "users effectively, ensuring that every answer is informative and reliable."
)

agent = MyAgent(system_prompt)
transcript = read_transcript("transcript.txt")
print(agent(transcript))
