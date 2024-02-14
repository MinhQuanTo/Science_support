import strawberry
import uuid
import datetime
import typing

# Definuje typ ID jako GraphQL ID, ale pak jej přepisuje na typ UUID
IDType = strawberry.ID
IDType = uuid.UUID

class BaseGQLModel:
    # Metoda určená k přepsání v odvozených třídách, získává loader pro načítání dat.
    @classmethod
    def getLoader(cls, info):
        pass
        
    # Asynchronně načítá a řeší referenci entity na základě jejího ID.
    @classmethod
    async def resolve_reference(cls, info: strawberry.types.Info, id: IDType):
        if id is None:
            return None
        loader = cls.getLoader(info)
        if isinstance(id, str): id = uuid.UUID(id)
        result = await loader.load(id)
        if result is not None:
            result.__strawberry_definition__ = cls.__strawberry_definition__ 
        return result


