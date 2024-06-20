from enum import Enum


class ModelType(Enum):
    GPT3 = "gpt-3.5-turbo"
    GPT4 = "gpt-4o"
    GLM4 = "glm-4-0520"
    GLM4V = "glm-4v"
    GLM4AIR = "glm-4-air"
    ZP_EMBEDDING = "embedding-2"
    OA_EMBEDDING_S = "text-embedding-3-small"
    OA_EMBEDDING_L = "text-embedding-3-large"
