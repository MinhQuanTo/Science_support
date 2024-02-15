import datetime
import strawberry
import uuid
from typing import List, Optional, Union, Annotated
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

# Definuje funkci pro získání "loaderu" z kontextu GraphQL.
def getLoader(info):
    return info.context["all"]

# Anotuje modely pro lenivé načítání s využitím Strawberry lazy loading.
GroupTypeGQLModel = Annotated["GroupTypeGQLModel", strawberry.lazy(".groupTypeGQLModel")]
MembershipGQLModel = Annotated["MembershipGQLModel", strawberry.lazy(".membershipGQLModel")]
RoleGQLModel = Annotated["RoleGQLModel", strawberry.lazy(".roleGQLModel")]

# Definuje GraphQL model pro skupinu s několika resolvery.
@strawberry.federation.type(keys=["id"], description="""Entity representing a group""")
class GroupGQLModel(BaseGQLModel):
    # Metoda pro získání loaderu pro skupiny.
    @classmethod
    def getLoader(cls, info):
        return getLoader(info).groups

    # Definice polí a resolvery pro základní atributy skupiny.
    id = resolve_id
    name = resolve_name
    name_en = resolve_name_en
    changedby = resolve_changedby
    created = resolve_created
    lastchange = resolve_lastchange
    createdby = resolve_createdby

    # Resolver pro validitu skupiny.
    @strawberry.field(description="""Group's validity (still exists?)""")
    def valid(self) -> bool:
        if not self.valid:
            return False
        else:
            return self.valid

    # Resolver pro typ skupiny.
    @strawberry.field(description="""Group's type (like Department)""")
    async def grouptype(
        self, info: strawberry.types.Info
    ) -> Union["GroupTypeGQLModel", None]:
        from .groupTypeGQLModel import GroupTypeGQLModel
        result = await GroupTypeGQLModel.resolve_reference(info, id=self.grouptype_id)
        return result

    # Resolver pro podskupiny.
    @strawberry.field(description="""Directly commanded groups""")
    async def subgroups(
        self, info: strawberry.types.Info
    ) -> List["GroupGQLModel"]:
        loader = getLoader(info).groups
        print(self.id)
        result = await loader.filter_by(mastergroup_id=self.id)
        return result

    # Resolver pro nadřazenou skupinu.
    @strawberry.field(description="""Commanding group""")
    async def mastergroup(
        self, info: strawberry.types.Info
    ) -> Union["GroupGQLModel", None]:
        result = await GroupGQLModel.resolve_reference(info, id=self.mastergroup_id)
        return result

    # Resolver pro členství ve skupině.
    @strawberry.field(description="""List of users who are member of the group""")
    async def memberships(
        self, info: strawberry.types.Info
    ) -> List["MembershipGQLModel"]:
        # result = await resolveMembershipForGroup(session,  self.id, skip, limit)
        # async with withInfo(info) as session:
        #     result = await resolveMembershipForGroup(session, self.id, skip, limit)
        #     return result

        loader = getLoader(info).memberships
        #print(self.id)
        result = await loader.filter_by(group_id=self.id)
        return result

    # Resolver pro role ve skupině.
    @strawberry.field(description="""List of roles in the group""")
    async def roles(self, info: strawberry.types.Info) -> List["RoleGQLModel"]:
        # result = await resolveRolesForGroup(session,  self.id)
        loader = getLoader(info).roles
        result = await loader.filter_by(group_id=self.id)
        return result


#####################################################################
#
# Special fields for query
#
#####################################################################
from .utils import createInputs
from dataclasses import dataclass
# Definuje vstupní filtr pro GraphQL query skupin.
# MembershipInputWhereFilter = Annotated["MembershipInputWhereFilter", strawberry.lazy(".membershipGQLModel")]
@createInputs
@dataclass
class GroupInputWhereFilter:
    name: str
    valid: bool
    from .membershipGQLModel import MembershipInputWhereFilter
    memberships: MembershipInputWhereFilter

# Resolver pro stránkování skupin.
@strawberry.field(description="""Returns a list of groups (paged)""")
async def group_page(
    self, info: strawberry.types.Info, skip: int = 0, limit: int = 10,
    where: Optional[GroupInputWhereFilter] = None
) -> List[GroupGQLModel]:
    wheredict = None if where is None else strawberry.asdict(where)
    loader = getLoader(info).groups
    result = await loader.page(skip, limit, where=wheredict)
    return result

# Resolver pro vyhledávání skupiny podle ID.
@strawberry.field(description="""Finds a group by its id""")
async def group_by_id(
    self, info: strawberry.types.Info, id: IDType
) -> Union[GroupGQLModel, None]:
    result = await GroupGQLModel.resolve_reference(info=info, id=id)
    return result

# Resolver pro vyhledávání skupin podle jména.
@strawberry.field(
    description="""Finds an user by letters in name and surname, letters should be atleast three"""
)
async def group_by_letters(
    self,
    info: strawberry.types.Info,
    validity: Union[bool, None] = None,
    letters: str = "",
) -> List[GroupGQLModel]:
    # result = await resolveGroupsByThreeLetters(session,  validity, letters)
    loader = getLoader(info).groups

    if len(letters) < 3:
        return []
    stmt = loader.getSelectStatement()
    model = loader.getModel()
    stmt = stmt.where(model.name.like(f"%{letters}%"))
    if validity is not None:
        stmt = stmt.filter_by(valid=True)

    result = await loader.execute_select(stmt)
    return result

# @strawberry.field(description="""Random university""")
# async def randomUniversity(
#     self, name: str, info: strawberry.types.Info
# ) -> GroupGQLModel:
#     async with withInfo(info) as session:
#         # newId = await randomDataStructure(session,  name)
#         newId = await randomDataStructure(session, name)
#         print("random university id", newId)
#         # result = await resolveGroupById(session,  newId)
#         result = await resolveGroupById(session, newId)
#         print("db response", result.name)
#         return result

#####################################################################
#
# Mutation section
#
#####################################################################
import datetime

# Definuje mutace pro aktualizaci a vložení skupiny.
@strawberry.input
class GroupUpdateGQLModel:
    # Definice vstupních polí pro aktualizaci skupiny.
    id: IDType
    lastchange: datetime.datetime
    name: Optional[str] = None
    grouptype_id: Optional[uuid.UUID] = None
    mastergroup_id: Optional[uuid.UUID] = None
    valid: Optional[bool] = None


@strawberry.input
class GroupInsertGQLModel:
    # Definice vstupních polí pro vytvoření nové skupiny.
    name: str
    id: Optional[uuid.UUID] = None
    grouptype_id: Optional[uuid.UUID] = None
    mastergroup_id: Optional[uuid.UUID] = None
    valid: Optional[bool] = None

@strawberry.type
class GroupResultGQLModel:
    # Typ pro výsledek operací s grupami.
    id: IDType = None
    msg: str = None

    @strawberry.field(description="""Result of group operation""")
    async def group(self, info: strawberry.types.Info) -> Union[GroupGQLModel, None]:
        print("GroupResultGQLModel", "group", self.id, flush=True)
        result = await GroupGQLModel.resolve_reference(info, self.id)
        print("GroupResultGQLModel", result.id, result.name, flush=True)
        return result

# Mutace pro aktualizaci skupiny.
@strawberry.mutation(description="""
    Allows a update of group, also it allows to change the mastergroup of the group
""")
async def group_update(self, info: strawberry.types.Info, group: GroupUpdateGQLModel) -> GroupResultGQLModel:
    loader = getLoader(info).groups
    
    updatedrow = await loader.update(group)
    #print(updatedrow, updatedrow.id, updatedrow.name, flush=True)
    if updatedrow is None:
        return GroupResultGQLModel(id=group.id, msg="fail")
    else:
        return GroupResultGQLModel(id=group.id, msg="ok")
    
# Mutace pro vytvoření nové skupiny.
@strawberry.mutation(description="""
    Allows a update of group, also it allows to change the mastergroup of the group
""")
async def group_insert(self, info: strawberry.types.Info, group: GroupInsertGQLModel) -> GroupResultGQLModel:
    loader = getLoader(info).groups
    
    updatedrow = await loader.insert(group)
    print("group_insert", updatedrow, updatedrow.id, updatedrow.name, flush=True)
    result = GroupResultGQLModel()
    result.id = updatedrow.id
    result.msg = "ok"

    if updatedrow is None:
        result.msg = "fail"
    
    return result

# Mutace pro aktualizaci nadřazené skupiny.
@strawberry.mutation(description="""
        Allows to assign the group to8 specified master group
    """)
async def group_update_master(self, 
    info: strawberry.types.Info, 
    master_id: IDType,
    group: GroupUpdateGQLModel) -> GroupResultGQLModel:
    loader = getLoader(info).groups
    
    result = GroupResultGQLModel()
    result.id = group.id
    result.msg = "ok"

    #use asyncio.gather here
    updatedrow = await loader.load(group.id)
    if updatedrow is None:
        result.msg = "fail"
        return result

    masterrow = await loader.load(master_id)
    if masterrow is None:
        result.msg = "fail"
        return result

    updatedrow.master_id = master_id
    updatedrow = await loader.update(updatedrow)
    
    if updatedrow is None:
        result.msg = "fail"
    
    return result
