import datetime
import strawberry
import uuid
from typing import List, Optional, Union, Annotated
import gql_ug.GraphTypeDefinitions
from .BaseGQLModel import BaseGQLModel, IDType
from ._GraphResolvers import (
    resolve_id,
    resolve_name,
    resolve_name_en,
    resolve_changedby,
    resolve_created,
    resolve_lastchange,
    resolve_createdby
)

def getLoader(info):
    return info.context["all"]

RoleGQLModel = Annotated["RoleGQLModel", strawberry.lazy(".roleGQLModel")]

@strawberry.federation.type(
    keys=["id"], description="""Entity representing a role type (like Dean)"""
)
class RoleTypeGQLModel(BaseGQLModel):
    @classmethod
    def getLoader(cls, info):
        return getLoader(info).roletypes

    id = resolve_id
    name = resolve_name
    name_en = resolve_name_en
    changedby = resolve_changedby
    created = resolve_created
    lastchange = resolve_lastchange
    createdby = resolve_createdby

    @strawberry.field(description="""List of roles with this type""")
    async def roles(self, info: strawberry.types.Info) -> List["RoleGQLModel"]:
        # result = await resolveRoleForRoleType(session,  self.id)
        loader = getLoader(info).roles
        result = await loader.filter_by(roletype_id=self.id)
        return result

#####################################################################
#
# Special fields for query
#
#####################################################################
from .utils import createInputs
from dataclasses import dataclass

@createInputs
@dataclass
class RoleTypeInputWhereFilter:
    name: str
    from .roleGQLModel import RoleInputWhereFilter
    roles: RoleInputWhereFilter

@strawberry.field(description="""Finds a role type by its id""")
async def role_type_by_id(
    self, info: strawberry.types.Info, id: IDType
) -> Union[RoleTypeGQLModel, None]:
    result = await RoleTypeGQLModel.resolve_reference(info, id)
    return result

@strawberry.field(description="""Finds all roles types paged""")
async def role_type_page(
    self, info: strawberry.types.Info, skip: int = 0, limit: int = 10,
    where: Optional[RoleTypeInputWhereFilter] = None
) -> List[RoleTypeGQLModel]:
    wheredict = None if where is None else strawberry.asdict(where)
    # result = await resolveRoleTypeAll(session,  skip, limit)
    loader = getLoader(info).roletypes
    result = await loader.page(skip, limit, where=wheredict)
    return result
    
#####################################################################
#
# Mutation section
#
#####################################################################
import datetime
@strawberry.input
class RoleTypeUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    name: Optional[str] = None
    name_en: Optional[str] = None

@strawberry.input
class RoleTypeInsertGQLModel:
    id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    name_en: Optional[str] = None

@strawberry.type
class RoleTypeResultGQLModel:
    id: IDType = None
    msg: str = None

    @strawberry.field(description="""Result of role type operation""")
    async def role_type(self, info: strawberry.types.Info) -> Union[RoleTypeGQLModel, None]:
        result = await RoleTypeGQLModel.resolve_reference(info, self.id)
        return result
    
@strawberry.mutation(description="""Updates existing roleType record""")
async def role_type_update(self, 
    info: strawberry.types.Info, 
    role_type: RoleTypeUpdateGQLModel

) -> RoleTypeResultGQLModel:
    print("role_type_update", role_type, flush=True)
    loader = getLoader(info).roletypes
    row = await loader.update(role_type)
    if row is not None:
        print("role_type_update", row, row.name, row.id, flush=True)
    result = RoleTypeResultGQLModel()
    result.msg = "ok"
    result.id = role_type.id
    if row is None:
        result.msg = "fail"
    
    return result

@strawberry.mutation(description="""Inserts a new roleType record""")
async def role_type_insert(self, 
    info: strawberry.types.Info, 
    role_type: RoleTypeInsertGQLModel

) -> RoleTypeResultGQLModel:
    #print("role_type_update", role_type, flush=True)
    loader = getLoader(info).roletypes
    row = await loader.insert(role_type)
    if row is not None:
        print("role_type_update", row, row.name, row.id, flush=True)
    result = RoleTypeResultGQLModel()
    result.msg = "ok"
    result.id = row.id       
    return result    