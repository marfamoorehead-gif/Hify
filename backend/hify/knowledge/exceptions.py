from hify.core.exceptions import ErrorCode, HifyBaseException


class KnowledgeNotFoundError(HifyBaseException):
    def __init__(self, knowledge_id: int):
        super().__init__(
            code=ErrorCode.KNOWLEDGE_NOT_FOUND,
            message=f"Knowledge base not found: {knowledge_id}",
        )


class DocumentImportError(HifyBaseException):
    def __init__(self, detail: str = "Document import failed"):
        super().__init__(code=ErrorCode.DOCUMENT_IMPORT_ERROR, message=detail)


class DocumentNotFoundError(HifyBaseException):
    def __init__(self, document_id: int):
        super().__init__(
            code=ErrorCode.DOCUMENT_NOT_FOUND,
            message=f"Document not found: {document_id}",
        )


class EmbeddingError(HifyBaseException):
    def __init__(self, detail: str = "Embedding failed"):
        super().__init__(code=ErrorCode.EMBEDDING_ERROR, message=detail)
