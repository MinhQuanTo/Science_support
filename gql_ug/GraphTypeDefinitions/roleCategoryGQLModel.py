import datetime
import strawberry
import uuid
from typing import List, Optional, Union, Annotated
from .BaseGQLModel import BaseGQLModel, IDType

# Imports resolver functions for the GraphQL model fields.
from ._GraphResolvers import (
    resolve_id,
    resolve_name,
    resolve_name_en,
    resolve_changedby,
    resolve_created,
    resolve_lastchange,
    resolve_createdby
)

# Function to retrieve a loader object from the GraphQL context. This loader is typically used for batching and caching database requests.
def getLoader(info):
    return info.context["all"]

# Annotation for the RoleTypeGQLModel to be lazily loaded to prevent circular dependencies.
RoleTypeGQLModel = Annotated["RoleTypeGQLModel", strawberry.lazy(".roleTypeGQLModel")]

# Defines a GraphQL model for RoleCategory, including its schema and resolver methods.
@strawberry.federation.type(
    keys=["id"], description="""Entity representing a role type (like Dean)"""
)
class RoleCategoryGQLModel(BaseGQLModel):
    # Class method to get the loader specific for role categories.
    @classmethod
    def getLoader(cls, info):
        return getLoader(info).rolecategories

    # Resolver methods for the model's fields.
    id = resolve_id
    name = resolve_name
    name_en = resolve_name_en
    changedby = resolve_changedby
    created = resolve_created
    lastchange = resolve_lastchange
    createdby = resolve_createdby

    # Async resolver to fetch a list of RoleTypeGQLModel instances associated with this RoleCategory.
    @strawberry.field(description="""List of roles with this type""")
    async def role_types(self, info: strawberry.types.Info) -> List["RoleTypeGQLModel"]:
        # result = await resolveRoleForRoleType(session,  self.id)
        loader = getLoader(info).roletypes
        rows = await loader.filter_by(category_id=self.id)
        return rows
    
#####################################################################
#
# Special fields for query
#
#####################################################################
# Function to retrieve a role category by its ID.
@strawberry.field(description="""Finds a role type by its id""")
async def role_category_by_id(
    self, info: strawberry.types.Info, id: IDType
) -> Union[RoleCategoryGQLModel, None]:
    result = await RoleCategoryGQLModel.resolve_reference(info,  id)
    return result

# Function to retrieve a paginated list of role categories.
@strawberry.field(description="""gets role category page""")
async def role_category_page(
    self, info: strawberry.types.Info, skip: Optional[int] = 0, limit: Optional[int] = 10
) -> List[RoleCategoryGQLModel]:
    loader = getLoader(info).rolecategories
    result = await loader.page(skip, limit)
    return result

#####################################################################
#
# Mutation section
#
#####################################################################
import datetime

# Input model for updating a role category.
@strawberry.input
class RoleCategoryUpdateGQLModel:
    id: IDType
    lastchange: datetime.datetime
    name: Optional[str] = None
    name_en: Optional[str] = None

# Input model for inserting a new role category.
@strawberry.input
class RoleCategoryInsertGQLModel:
    id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    name_en: Optional[str] = None

# GraphQL model for the result of a role category operation.
@strawberry.type
class RoleCategoryResultGQLModel:
    id: IDType = None
    msg: str = None

    # Resolver for the operation result, returning the affected RoleCategoryGQLModel instance.
    @strawberry.field(description="""Result of role category operation""")
    async def role_category(self, info: strawberry.types.Info) -> Union[RoleCategoryGQLModel, None]:
        result = await RoleCategoryGQLModel.resolve_reference(info, self.id)
        return result

# Mutation to update an existing role category.
@strawberry.mutation(description="""Updates a role category""")
async def role_category_update(self, 
    info: strawberry.types.Info, 
    role_category: RoleCategoryUpdateGQLModel

) -> RoleCategoryResultGQLModel:

    loader = getLoader(info).rolecategories
    row = await loader.update(role_category)

    result = RoleCategoryResultGQLModel()
    result.msg = "ok"
    result.id = role_category.id
    if row is None:
        result.msg = "fail"
    else:
        result.id = row.id

    
    return result

# Mutation to insert a new role category.
@strawberry.mutation(description="""Inserts a role category""")
async def role_category_insert(self, 
    info: strawberry.types.Info, 
    role_category: RoleCategoryInsertGQLModel

) -> RoleCategoryResultGQLModel:

    loader = getLoader(info).rolecategories
    row = await loader.insert(role_category)

    result = RoleCategoryResultGQLModel()
    result.msg = "ok"
    result.id = row.id
    
    return result
