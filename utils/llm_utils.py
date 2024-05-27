
import os
import tiktoken
from openai import OpenAI
# 设置环境变量，用于存储OpenAI的API密钥
OPenaiClient = OpenAI(
    api_key=os.environ.get('OPENAI_API_KEY')
)
class LLM_Response():
    def get_openai_response(    
        self,
        systemset:str,
        prompt:str
    ):
        response = OPenaiClient.chat.completions.create(
            # model="gpt-3.5-turbo-16k",
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content":systemset },
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content



#token计算办法
def token_compute(
    messages,
    model="gpt-3.5-turbo-0613"
)->int:
        """
            返回当前信息token的数值
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            print("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")
        if model in {
            "gpt-3.5-turbo-0613",
            "gpt-3.5-turbo-16k-0613",
            "gpt-4-0314",
            "gpt-4-32k-0314",
            "gpt-4-0613",
            "gpt-4-32k-0613",
            }:
            tokens_per_message = 3
        elif model == "gpt-3.5-turbo-0301":
            tokens_per_message = 4
        elif "gpt-3.5-turbo" in model:
            print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
            return token_compute(messages, model="gpt-3.5-turbo-0613")
        elif "gpt-4" in model:
            print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
            return token_compute(messages, model="gpt-4-0613")
        else:
            raise NotImplementedError(
                f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
            )
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            num_tokens += len(encoding.encode(message))
        num_tokens += 3  # every reply is primed with <|im_start|>assistant<|im_sep|>
        return num_tokens
    