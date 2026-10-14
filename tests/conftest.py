import os
os.environ['OPENAI_API_KEY']=''
os.environ['JWT_SECRET_KEY']='synthetic-test-only-not-a-credential-0000000'
os.environ['PYTHON_DOTENV_DISABLED']='1'
import httpx
def denied(*args,**kwargs): raise RuntimeError('Network disabled in security tests')
async def denied_async(*args,**kwargs): raise RuntimeError('Network disabled in security tests')
httpx.HTTPTransport.handle_request=denied
httpx.AsyncHTTPTransport.handle_async_request=denied_async
