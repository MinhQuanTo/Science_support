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

# Funkce pro získání loaderu z kontextu GraphQL dotazu.
def getLoader(info):
    return info.context["all"]

# Anotace pro lenivé načítání modelu GroupGQLModel.
GroupGQLModel = Annotated["GroupGQLModel", strawberry.lazy(".groupGQLModel")]

# Definice GraphQL modelu pro typ skupiny s příslušnými resolvery a metodami.
@strawberry.federation.type(
    keys=["id"], description="""Entity representing a group type (like Faculty)"""
)
class GroupTypeGQLModel(BaseGQLModel):
    # Metoda pro získání loaderu specifického pro typy skupin.
    @classmethod
    def getLoader(cls, info):
        return getLoader(info).grouptypes

    # Definice polí modelu s použitím předem definovaných resolvers.
    id = resolve_id
    name = resolve_name
    name_en = resolve_name_en
    changedby = resolve_changedby
    created = resolve_created
    lastchange = resolve_lastchange
    createdby = resolve_createdby

    # Resolver pro získání seznamu skupin, které mají tento typ.
    @strawberry.field(description="""List of groups which have this type""")
    async def groups(
        self, info: strawberry.types.Info
    ) -> List["GroupGQLModel"]:
        # result = await resolveGroupForGroupType(session,  self.id)
        loader = getLoader(info).groups
        result = await loader.filter_by(grouptype_id=self.id)
        return result

#####################################################################
#
# Special fields for query
#
#####################################################################
from .utils import createInputs
from dataclasses import dataclass
# MembershipInputWhereFilter = Annotated["MembershipInputWhereFilter", strawberry.lazy(".membershipGQLModel")]
# Definice vstupního filtru pro dotazování na typy skupin.
@createInputs
@dataclass
class GroupTypeInputWhereFilter:
    name: str
    valid: bool
    # from .membershipGQLModel import MembershipInputWhereFilter
    # memberships: MembershipInputWhereFilter

# Resolver pro stránkované získání typů skupin.
@strawberry.field(description="""Returns a list of groups types (paged)""")
async def group_type_page(
    self, info: strawberry.types.Info, skip: int = 0, limit: int = 20,
    where: Optional[GroupTypeInputWhereFilter] = None
) -> List[GroupTypeGQLModel]:
    wheredict = None if where is None else strawberry.asdict(where)
    loader = getLoader(info).grouptypes
    result = await loader.page(skip, limit, where=wheredict)
    return result

# Resolver pro získání typu skupiny podle ID.
@strawberry.field(description="""Finds a group type by its id""")
async def group_type_by_id(
    self, info: strawberry.types.Info, id: IDType
) -> Union[GroupTypeGQLModel, None]:
    # result = await resolveGroupTypeById(session,  id)
    result = await GroupTypeGQLModel.resolve_reference(info, id)
    return result

#####################################################################
#
# Mutation section
#
#####################################################################
import datetime

# Definice input modelů pro mutace aktualizace a vložení typů skupin.
@strawberry.input
class GroupTypeUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    name: Optional[str] = None
    name_en: Optional[str] = None

@strawberry.input
class GroupTypeInsertGQLModel:
    id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    name_en: Optional[str] = None

# Definice typu pro výsledek operací s typy skupin.
@strawberry.type
class GroupTypeResultGQLModel:
    id: IDType = None
    msg: str = None

    @strawberry.field(description="""Result of grouptype operation""")
    async def group_type(self, info: strawberry.types.Info) -> Union[GroupTypeGQLModel, None]:
        result = await GroupTypeGQLModel.resolve_reference(info, self.id)
        return result

# Mutace pro aktualizaci typu skupiny.
@strawberry.mutation(description="""
        Allows a update of group, also it allows to change the mastergroup of the group
    """)
async def group_type_update(self, info: strawberry.types.Info, group_type: GroupTypeUpdateGQLModel) -> GroupTypeResultGQLModel:
    loader = getLoader(info).grouptypes
    
    updatedrow = await loader.update(group_type)
    result = GroupTypeResultGQLModel()
    result.msg = "ok"
    result.id = group_type.id
    if updatedrow is None:
        result.msg = "fail"
    
    return result

# Mutace pro vložení nového typu skupiny.
@strawberry.mutation(description="""
    Inserts a group
""")
async def group_type_insert(self, info: strawberry.types.Info, group_type: GroupTypeInsertGQLModel) -> GroupTypeResultGQLModel:
    loader = getLoader(info).grouptypes
    
    updatedrow = await loader.insert(group_type)
    result = GroupTypeResultGQLModel()
    result.id = updatedrow.id
    result.msg = "ok"

    if updatedrow is None:
        result.msg = "fail"
    
    return result    
