from starlette.requests import HTTPConnection

from relationship_os.application.container import RuntimeContainer


def get_container(connection: HTTPConnection) -> RuntimeContainer:
    return connection.app.state.container
