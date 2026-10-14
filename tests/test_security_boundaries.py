import pathlib,types
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend import main
from backend.deps import get_current_user,check_rate_limit
from backend.routes import bulk


def setup_function():
    main.app.dependency_overrides.clear()


def test_missing_token_rejected():
    response=TestClient(main.app).get('/api/v1/bulk/jobs')
    assert response.status_code in {401,403}


def test_unmounted_integrations_and_trends():
    client=TestClient(main.app)
    assert client.post('/api/v1/integrations/zapier/generate',json={'topic':'synthetic'}).status_code==404
    assert client.post('/api/v1/trends/auto-generate',json={}).status_code==404


def test_bulk_dispatch_disabled_before_paid_work():
    main.app.dependency_overrides[check_rate_limit]=lambda:types.SimpleNamespace(id=1,is_admin=False)
    response=TestClient(main.app).post('/api/v1/bulk/generate',files={'file':('synthetic.csv',b'topic\nSynthetic\n','text/csv')})
    assert response.status_code==503


def test_foreign_bulk_job_not_visible():
    main.app.dependency_overrides[get_current_user]=lambda:types.SimpleNamespace(id=1,is_admin=False)
    bulk.bulk_jobs_db['synthetic']={'user_id':2}
    client=TestClient(main.app)
    assert client.get('/api/v1/bulk/status/synthetic').status_code==404
    assert client.delete('/api/v1/bulk/synthetic').status_code==404
    assert client.get('/api/v1/bulk/jobs').json()['jobs']==[]


def test_foreign_media_denied_and_owned_media_served(tmp_path):
    main.settings.output_dir=tmp_path
    (tmp_path/'fixture.mp4').write_bytes(b'synthetic fixture; not real media')
    main.app.dependency_overrides[get_current_user]=lambda:types.SimpleNamespace(id=1,is_admin=False)
    class Session:
        async def __aenter__(self):return self
        async def __aexit__(self,*args):pass
        async def execute(self,*args):return types.SimpleNamespace(scalars=lambda:types.SimpleNamespace(all=lambda:[types.SimpleNamespace(user_id=2)]))
    with patch.object(main,'async_session',Session):
        assert TestClient(main.app).get('/out/fixture.mp4').status_code==404
    class OwnedSession(Session):
        async def execute(self,*args):return types.SimpleNamespace(scalars=lambda:types.SimpleNamespace(all=lambda:[types.SimpleNamespace(user_id=1)]))
    with patch.object(main,'async_session',OwnedSession):
        response=TestClient(main.app).get('/out/fixture.mp4')
        assert response.status_code==200 and response.content.startswith(b'synthetic')


def test_media_path_escape_rejected(tmp_path):
    main.settings.output_dir=tmp_path
    main.app.dependency_overrides[get_current_user]=lambda:types.SimpleNamespace(id=1,is_admin=False)
    assert TestClient(main.app).get('/out/..%5Cprivate.mp4').status_code==404


def test_generation_inputs_bounded():
    from backend.routes.generate import GenerateRequest,MagicGenerateRequest
    import pytest
    with pytest.raises(ValueError):MagicGenerateRequest(topic='x'*2001)
    with pytest.raises(ValueError):GenerateRequest(topic='Synthetic',duration='9999s')


def test_signup_disabled_by_default():
    response=TestClient(main.app).post('/api/v1/auth/signup',json={'email':'fixture@example.com','password':'synthetic-test-password'})
    assert response.status_code==403


def test_received_body_and_host_bounded():
    client=TestClient(main.app)
    assert client.post('/api/v1/magic',content=iter([b'x'*16000,b'x'*16001])).status_code==413
    assert client.get('/health',headers={'Host':'attacker.example'}).status_code==400


def test_jwt_valid_signature_accepted_and_forgery_rejected():
    import asyncio
    import pytest
    from fastapi import HTTPException
    from fastapi.security import HTTPAuthorizationCredentials
    from backend import deps
    user=types.SimpleNamespace(id=1,email='fixture@example.com',is_active=True)
    class DB:
        async def execute(self,*args):return types.SimpleNamespace(scalar_one_or_none=lambda:user)
    token=deps.create_access_token({'sub':user.email})
    result=asyncio.run(deps.get_current_user(HTTPAuthorizationCredentials(scheme='Bearer',credentials=token),DB()))
    assert result.id==1
    with pytest.raises(HTTPException):
        asyncio.run(deps.get_current_user(HTTPAuthorizationCredentials(scheme='Bearer',credentials=token+'forged'),DB()))
