import json
import pytest
import yaml
from os.path import join, dirname, abspath

from aiohttp import web
from aiohttp_swagger import *


pytestmark = pytest.mark.asyncio


async def ping(request):
    """
    ---
    description: This end-point allow to test that service is up.
    tags:
    - Health check
    produces:
    - text/plain
    responses:
        "200":
            description: successful operation. Return "pong" text
        "405":
            description: invalid HTTP Method
    """
    return web.Response(text="pong")


async def undoc_ping(request):
    return web.Response(text="pong")


async def users_with_data_def(request):
    """
    ---
    description: This endpoint returns user which is defined though data definition during initialization.
    tags:
    - Users
    produces:
    - application/json
    responses:
        "200":
            description: Successful operation, returns User object nested permission list
            schema:
              $ref: '#/definitions/User'
    """
    return web.Response(text="pong")


class ClassView(web.View):
    def _irrelevant_method(self):
        pass

    async def get(self):
        """
        ---
        description: Get resources
        tags:
        - Class View
        produces:
        - text/plain
        responses:
            "200":
                description: successful operation.
            "405":
                description: invalid HTTP Method
        """
        return web.Response(text="OK")

    async def post(self):
        """
        ---
        description: Post resources
        tags:
        - Class View
        produces:
        - text/plain
        responses:
            "200":
                description: successful operation.
            "405":
                description: invalid HTTP Method
        """
        return web.Response(text="OK")

    async def patch(self):
        """
        This method is undocumented in the swagger sense.
        """
        return web.Response(text="OK")


@swagger_path(abspath(join(dirname(__file__))) + '/data/partial_swagger.yaml')
async def ping_partial(request):
    return web.Response(text="pong")


async def test_swagger_ui(aiohttp_client):
    TESTS_PATH = abspath(join(dirname(__file__)))

    app = web.Application()
    setup_swagger(app,
                  swagger_from_file=TESTS_PATH + "/data/example_swagger.yaml",
                  ui_version=3
                  )

    client = await aiohttp_client(app)
    resp1 = await client.get('/api/doc')
    assert resp1.status == 200
    retrieved = await resp1.text()
    loaded = open(join(TESTS_PATH, "..", "aiohttp_swagger/swagger_ui3/index.html")).read()
    loaded = loaded.replace("##STATIC_PATH##", "/api/doc/swagger_static")
    loaded = loaded.replace("##SWAGGER_CONFIG##", "/api/doc/swagger.json")
    loaded = loaded.replace("##SWAGGER_VALIDATOR_URL##", '')
    assert retrieved == loaded


async def test_swagger_file_url(aiohttp_client):
    TESTS_PATH = abspath(join(dirname(__file__)))

    app = web.Application()
    setup_swagger(app,
                  ui_version=3,
                  swagger_from_file=TESTS_PATH + "/data/example_swagger.yaml")

    client = await aiohttp_client(app)
    resp1 = await client.get('/api/doc/swagger.json')
    assert resp1.status == 200
    result = await resp1.json()
    assert '/example1' in result['paths']
    assert '/example2' in result['paths']
    assert 'API Title' in result['info']['title']


async def test_partial_swagger_file(aiohttp_client):
    app = web.Application()
    app.router.add_route('GET', "/ping-partial", ping_partial)
    setup_swagger(app, ui_version=3)

    client = await aiohttp_client(app)
    resp1 = await client.get('/api/doc/swagger.json')
    assert resp1.status == 200
    result = await resp1.json()
    assert '/ping-partial' in result['paths']


async def test_custom_swagger(aiohttp_client):
    app = web.Application()
    app.router.add_route('GET', "/ping", ping)
    description = "Test Custom Swagger"
    setup_swagger(app,
                  ui_version=3,
                  swagger_url="/api/v1/doc",
                  description=description,
                  title="Test Custom Title",
                  api_version="1.0.0",
                  contact="my.custom.contact@example.com")

    client = await aiohttp_client(app)
    resp1 = await client.get('/api/v1/doc/swagger.json')
    assert resp1.status == 200
    result = await resp1.json()
    assert '/ping' in result['paths']
    assert 'Test Custom Title' in result['info']['title']


async def test_swagger_home_decorator(aiohttp_client):
    app = web.Application()
    app.router.add_route('GET', "/ping", ping)
    description = "Test Custom Swagger"
    setup_swagger(app,
                  ui_version=3,
                  swagger_url="/api/v1/doc",
                  description=description,
                  title="Test Custom Title",
                  api_version="1.0.0",
                  contact="my.custom.contact@example.com",
                  swagger_home_decor=lambda x: x)

    client = await aiohttp_client(app)
    resp1 = await client.get('/api/v1/doc/swagger.json')
    assert resp1.status == 200
    result = await resp1.json()
    assert '/ping' in result['paths']
    assert 'Test Custom Title' in result['info']['title']


async def test_swagger_def_decorator(aiohttp_client):
    app = web.Application()
    app.router.add_route('GET', "/ping", ping)
    description = "Test Custom Swagger"
    setup_swagger(app,
                  ui_version=3,
                  swagger_url="/api/v1/doc",
                  description=description,
                  title="Test Custom Title",
                  api_version="1.0.0",
                  contact="my.custom.contact@example.com",
                  swagger_def_decor=lambda x: x)

    client = await aiohttp_client(app)
    resp1 = await client.get('/api/v1/doc/swagger.json')
    assert resp1.status == 200
    result = await resp1.json()
    assert '/ping' in result['paths']
    assert 'Test Custom Title' in result['info']['title']


@pytest.fixture
def swagger_info():
    filename = abspath(join(dirname(__file__))) + "/data/example_swagger.yaml"
    return yaml.full_load(open(filename).read())


async def test_swagger_info(aiohttp_client, swagger_info):
    app = web.Application()
    app.router.add_route('GET', "/ping", ping)
    description = "Test Custom Swagger"
    setup_swagger(app,
                  ui_version=3,
                  swagger_url="/api/v1/doc",
                  swagger_info=swagger_info)

    client = await aiohttp_client(app)
    resp1 = await client.get('/api/v1/doc/swagger.json')
    assert resp1.status == 200
    result = await resp1.json()
    assert '/example1' in result['paths']
    assert '/example2' in result['paths']
    assert 'API Title' in result['info']['title']


async def test_undocumented_fn(aiohttp_client):
    app = web.Application()
    app.router.add_route('GET', "/undoc_ping", undoc_ping)
    setup_swagger(app, ui_version=3)
    client = await aiohttp_client(app)
    resp = await client.get('/undoc_ping')
    assert resp.status == 200
    swagger_resp1 = await client.get('/api/doc/swagger.json')
    assert swagger_resp1.status == 200
    result = await swagger_resp1.json()
    assert not result['paths']


async def test_wrong_method(aiohttp_client):
    app = web.Application()
    app.router.add_route('POST', "/post_ping", ping)
    setup_swagger(app, ui_version=3)
    client = await aiohttp_client(app)
    # GET
    swagger_resp1 = await client.get('/api/doc/swagger.json')
    assert swagger_resp1.status == 200
    result = await swagger_resp1.json()
    assert "/post_ping" in result['paths']
    assert "post" in result['paths']["/post_ping"]
    resp = await client.get('/post_ping')
    assert resp.status == 405


async def test_class_view(aiohttp_client):
    app = web.Application()
    app.router.add_route('*', "/class_view", ClassView)
    setup_swagger(app, ui_version=3)

    client = await aiohttp_client(app)
    # GET
    resp = await client.get('/class_view')
    assert resp.status == 200
    text = await resp.text()
    assert 'OK' in text
    swagger_resp1 = await client.get('/api/doc/swagger.json')
    assert swagger_resp1.status == 200
    result = await swagger_resp1.json()
    assert "/class_view" in result['paths']
    assert "get" in result['paths']["/class_view"]
    assert "post" in result['paths']["/class_view"]

    # POST
    resp = await client.post('/class_view')
    assert resp.status == 200
    text = await resp.text()
    assert 'OK' in text
    result = await swagger_resp1.json()
    assert "/class_view" in result['paths']
    assert "get" in result['paths']["/class_view"]
    assert "post" in result['paths']["/class_view"]

    # Undocumented PATCH
    resp = await client.patch('/class_view')
    assert resp.status == 200
    text = await resp.text()
    assert 'OK' in text
    result = await swagger_resp1.json()
    assert "/class_view" in result['paths']
    assert "patch" not in result['paths']["/class_view"]


async def test_data_defs(aiohttp_client):
    TESTS_PATH = abspath(join(dirname(__file__)))
    file = open(TESTS_PATH + "/data/example_data_definitions.json")
    app = web.Application()
    app.router.add_route('GET', "/users", users_with_data_def)
    setup_swagger(app, ui_version=3, definitions=json.loads(file.read()))
    file.close()

    client = await aiohttp_client(app)
    swagger_resp1 = await client.get('/api/doc/swagger.json')
    assert swagger_resp1.status == 200
    result = await swagger_resp1.json()
    assert 'User' in result['components']['schemas']
    assert 'Permission' in result['components']['schemas']
    assert result['components']['schemas']['User']['properties']['permissions']['items']['$ref'] is not None
    assert result['components']['schemas']['Permission']['properties']['permission_param_3']['default'] is not None


async def test_parameter_defs(aiohttp_client):
    TESTS_PATH = abspath(join(dirname(__file__)))
    with open(TESTS_PATH + "/data/example_data_parameters.json") as file:
        app = web.Application()
        app.router.add_route('GET', "/users", users_with_data_def)
        setup_swagger(app, ui_version=3, parameters=json.loads(file.read()))

    client = await aiohttp_client(app)
    swagger_resp1 = await client.get('/api/doc/swagger.json')
    assert swagger_resp1.status == 200
    result = await swagger_resp1.json()
    assert 'XAppNameHeader' in result['components']['parameters']
    assert result['components']['parameters']['XAppNameHeader']['schema']['default'] is not None


async def test_sub_app(aiohttp_client):
    sub_app = web.Application()
    sub_app.router.add_route('*', "/class_view", ClassView)
    setup_swagger(sub_app, ui_version=3, api_base_url='/sub_app')
    app = web.Application()
    app.add_subapp(prefix='/sub_app', subapp=sub_app)

    client = await aiohttp_client(app)
    # GET
    resp = await client.get('/sub_app/class_view')
    assert resp.status == 200
    text = await resp.text()
    assert 'OK' in text
    swagger_resp1 = await client.get('/sub_app/api/doc/swagger.json')
    assert swagger_resp1.status == 200
    result = await swagger_resp1.json()
    assert "/class_view" in result['paths']
    assert "get" in result['paths']["/class_view"]
    assert "post" in result['paths']["/class_view"]
