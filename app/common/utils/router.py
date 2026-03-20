from fastapi import APIRouter
from typing_extensions import Annotated
from pydantic import StringConstraints
from typing import List, Optional, Union
from enum import Enum

VersionType = Annotated[str, StringConstraints(pattern=r"^[1-9]\d*$")]

class VersionRouter(APIRouter):
    def __init__(self,
                  version: VersionType,
                   path: str,
                   tags: Optional[List[Union[str, Enum]]] ):
        self._validate_version(version)
        self.version = version
        self.prefix = f"/v{version}/{path}"
        super().__init__(prefix=self.prefix, tags=tags)

    def _validate_version(self, version: str):
        if not version.isdigit() or int(version) <= 0:
            raise ValueError("Version must be a string representing a positive integer string.")