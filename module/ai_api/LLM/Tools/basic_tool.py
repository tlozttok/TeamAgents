




import json
from typing import Any, Callable, Dict, List


class ToolParameter:
    def __init__(self, name: str, description: str, type: str, required: bool = True) -> None:
        self.name = name
        self.description = description
        self.type = type


class Tool:
    name: str
    description: str
    parameters: List[ToolParameter]
    required: List[str]
    function: Callable[[Any,], dict]

    def __init__(self, name: str, description: str, function: Callable[[str], str]) -> None:
        self.name = name
        self.description = description
        self.parameters = []
        self.required = []
        self.function = function

    def to_dict(self) -> Dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        param.name: {
                            "type": param.type,
                            "description": param.description
                        }
                        for param in self.parameters
                    },
                    "required": self.required
                }
            }
        }

    def call(self,para:str):
        para_dict=json.loads(para)
        result=self.function(**para_dict)
        return json.dumps(result)
