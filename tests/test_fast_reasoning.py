import json
import unittest
from unittest.mock import patch
from cloud_backend import main

class Response:
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self): return json.dumps({'choices':[{'message':{'content':'A concise answer.'}}]}).encode()

class FastReasoningTests(unittest.TestCase):
    def payload(self,model,quick):
        with patch.dict('os.environ',{'GROQ_API_KEY':'test-placeholder'}),patch.object(main,'GROQ_MODEL',model),patch.object(main,'urlopen',return_value=Response()) as request:
            main._groq_reply('A simple question','Be helpful',quick=quick)
            return json.loads(request.call_args.args[0].data)
    def test_simple_supported_models_use_low_reasoning(self):
        for model in ('openai/gpt-oss-20b','openai/gpt-oss-120b'):
            self.assertEqual(self.payload(model,True)['reasoning_effort'],'low')
    def test_full_tasks_keep_default_reasoning_and_output_budget(self):
        data=self.payload('openai/gpt-oss-20b',False)
        self.assertNotIn('reasoning_effort',data)
        self.assertEqual(data['max_tokens'],1024)
    def test_other_models_do_not_receive_unsupported_parameter(self):
        self.assertNotIn('reasoning_effort',self.payload('llama-3.1-8b-instant',True))
