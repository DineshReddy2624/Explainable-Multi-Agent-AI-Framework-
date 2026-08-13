from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from core.response import StandardResponse

class BaseAppException(Exception):
    def __init__(self, message: str, status_code: int = 400, details: any = None):
        self.message = message
        self.status_code = status_code
        self.details = details

class DatasetNotFoundException(BaseAppException):
    def __init__(self, dataset_id: int):
        super().__init__(f"Dataset with ID {dataset_id} not found.", status_code=404)

class AgentExecutionException(BaseAppException):
    def __init__(self, agent_name: str, reason: str):
        super().__init__(f"Agent [{agent_name}] execution failed: {reason}", status_code=500)

async def app_exception_handler(request: Request, exc: BaseAppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=StandardResponse.fail(message=exc.message, errors=exc.details).model_dump()
    )
