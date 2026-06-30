class ServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        # DB/service 모듈은 FastAPI에 직접 의존하지 않고 업무 실패 정보만 전달한다.
        self.message = message
        self.status_code = status_code
        super().__init__(message)
