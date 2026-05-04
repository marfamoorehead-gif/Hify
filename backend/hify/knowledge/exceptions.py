from hify.core.exceptions import BizException, ErrorCode


class KnowledgeNotFoundError(BizException):
    def __init__(self, knowledge_id: int):
        super().__init__(
            ErrorCode.KNOWLEDGE_NOT_FOUND,
            message=f"Knowledge base not found: {knowledge_id}",
        )


class DocumentImportError(BizException):
    def __init__(self, detail: str | None = None):
        super().__init__(ErrorCode.DOCUMENT_IMPORT_ERROR, message=detail)


class DocumentNotFoundError(BizException):
    def __init__(self, document_id: int):
        super().__init__(
            ErrorCode.DOCUMENT_NOT_FOUND,
            message=f"Document not found: {document_id}",
        )


class EmbeddingError(BizException):
    def __init__(self, detail: str | None = None):
        super().__init__(ErrorCode.EMBEDDING_ERROR, message=detail)
