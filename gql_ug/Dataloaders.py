import logging
from uoishelpers.dataloaders import createIdLoader, createFkeyLoader
import datetime
import aiohttp
import asyncio
import os
from aiodataloader import DataLoader

from gql_ug.DBDefinitions import (
    UserModel,
    MembershipModel,
    GroupModel,
    GroupTypeModel,
    RoleModel,
    RoleTypeModel,
    RoleCategoryModel
)

from uoishelpers.resolvers import select, update, delete



def prepareSelect(model, where: dict):   
    usedTables = [model.__tablename__]
    from sqlalchemy import select, and_, or_
    baseStatement = select(model)
    # stmt = select(GroupTypeModel).join(GroupTypeModel.groups.property.target).filter(GroupTypeModel.groups.property.target.c.name == "22-5KB")
    # type(GroupTypeModel.groups.property) sqlalchemy.orm.relationships.RelationshipProperty
    # GroupTypeModel.groups.property.entity.class_
    def limitDict(input):
        if isinstance(input, list):
            return [limitDict(item) for item in input]
        if not isinstance(input, dict):
            # print("limitDict", input)
            return input
        result = {key: limitDict(value) if isinstance(value, dict) else value for key, value in input.items() if value is not None}
        return result
    
    def convertAnd(model, name, listExpr):
        assert len(listExpr) > 0, "atleast one attribute in And expected"
        results = [convertAny(model, w) for w in listExpr]
        return and_(*results)

    def convertOr(model, name, listExpr):
        # print("enter convertOr", listExpr)
        assert len(listExpr) > 0, "atleast one attribute in Or expected"
        results = [convertAny(model, w) for w in listExpr]
        return or_(*results)

    def convertAttributeOp(model, name, op, value):
        # print("convertAttributeOp", type(model))
        # print("convertAttributeOp", model, name, op, value)
        column = getattr(model, name)
        assert column is not None, f"cannot map {name} to model {model.__tablename__}"
        opMethod = getattr(column, op)
        assert opMethod is not None, f"cannot map {op} to attribute {name} of model {model.__tablename__}"
        return opMethod(value)

    def convertRelationship(model, attributeName, where, opName, opValue):
        # print("convertRelationship", model, attributeName, where, opName, opValue)
        # GroupTypeModel.groups.property.entity.class_
        targetDBModel = getattr(model, attributeName).property.entity.class_
        # print("target", type(targetDBModel), targetDBModel)

        nonlocal baseStatement
        if targetDBModel.__tablename__ not in usedTables:
            baseStatement = baseStatement.join(targetDBModel)
            usedTables.append(targetDBModel.__tablename__)
        #return convertAttribute(targetDBModel, attributeName, opValue)
        return convertAny(targetDBModel, opValue)
        
        # stmt = select(GroupTypeModel).join(GroupTypeModel.groups.property.target).filter(GroupTypeModel.groups.property.target.c.name == "22-5KB")
        # type(GroupTypeModel.groups.property) sqlalchemy.orm.relationships.RelationshipProperty

    def convertAttribute(model, attributeName, where):
        woNone = limitDict(where)
        #print("convertAttribute", model, attributeName, woNone)
        keys = list(woNone.keys())
        assert len(keys) == 1, "convertAttribute: only one attribute in where expected"
        opName = keys[0]
        opValue = woNone[opName]

        ops = {
            "_eq": "__eq__",
            "_lt": "__lt__",
            "_le": "__le__",
            "_gt": "__gt__",
            "_ge": "__ge__",
            "_in": "in_",
            "_like": "like",
            "_ilike": "ilike",
            "_startswith": "startswith",
            "_endswith": "endswith",
        }

        opName = ops.get(opName, None)
        # if opName is None:
        #     print("op", attributeName, opName, opValue)
        #     result = convertRelationship(model, attributeName, woNone, opName, opValue)
        # else:
        result = convertAttributeOp(model, attributeName, opName, opValue)
        return result
        
    def convertAny(model, where):
        
        woNone = limitDict(where)
        # print("convertAny", woNone, flush=True)
        keys = list(woNone.keys())
        # print(keys, flush=True)
        # print(woNone, flush=True)
        assert len(keys) == 1, "convertAny: only one attribute in where expected"
        key = keys[0]
        value = woNone[key]
        
        convertors = {
            "_and": convertAnd,
            "_or": convertOr
        }
        #print("calling", key, "convertor", value, flush=True)
        #print("value is", value, flush=True)
        convertor = convertors.get(key, convertAttribute)
        convertor = convertors.get(key, None)
        modelAttribute = getattr(model, key, None)
        if (convertor is None) and (modelAttribute is None):
            print(dir(model))
            print(modelAttribute)
            assert False, f"cannot recognize {model}.{key} on {woNone}"
        if (modelAttribute is not None):
            property = getattr(modelAttribute, "property", None)
            target = getattr(property, "target", None)
            # print("modelAttribute", modelAttribute, target)
            if target is None:
                result = convertAttribute(model, key, value)
            else:
                result = convertRelationship(model, key, where, key, value)
        else:
            result = convertor(model, key, value)
        return result
    
    filterStatement = convertAny(model, limitDict(where))
    result = baseStatement.filter(filterStatement)
    return result

def createIdLoader(asyncSessionMaker, dbModel) :

    mainstmt = select(dbModel)
    filtermethod = dbModel.id.in_
    class Loader(DataLoader):
        async def batch_load_fn(self, keys):
            #print('batch_load_fn', keys, flush=True)
            async with asyncSessionMaker() as session:
                statement = mainstmt.filter(filtermethod(keys))
                rows = await session.execute(statement)
                rows = rows.scalars()
                #return rows
                datamap = {}
                for row in rows:
                    datamap[row.id] = row
                result = [datamap.get(id, None) for id in keys]
                return result

        async def insert(self, entity, extraAttributes={}):
            newdbrow = dbModel()
            newdbrow = update(newdbrow, entity, extraAttributes)
            async with asyncSessionMaker() as session:
                session.add(newdbrow)
                await session.commit()
            return newdbrow

        async def update(self, entity, extraValues={}):
            async with asyncSessionMaker() as session:
                statement = mainstmt.filter_by(id=entity.id)
                rows = await session.execute(statement)
                rows = rows.scalars()
                rowToUpdate = next(rows, None)

                if rowToUpdate is None:
                    return None

                dochecks = hasattr(rowToUpdate, 'lastchange')             
                checkpassed = True  
                if (dochecks):
                    if (entity.lastchange != rowToUpdate.lastchange):
                        result = None
                        checkpassed = False                        
                    else:
                        entity.lastchange = datetime.datetime.now()
                if checkpassed:
                    rowToUpdate = update(rowToUpdate, entity, extraValues=extraValues)
                    await session.commit()
                    result = rowToUpdate
                    self.registerResult(result)               
            return result

        async def delete(self, id):
            statement = delete(dbModel).where(dbModel.id==id)
            async with asyncSessionMaker() as session:
                result = await session.execute(statement)
                await session.commit()
                self.clear(id)
                return result

        def registerResult(self, result):
            self.clear(result.id)
            self.prime(result.id, result)
            return result

        def getSelectStatement(self):
            return select(dbModel)
        
        def getModel(self):
            return dbModel
        
        def getAsyncSessionMaker(self):
            return asyncSessionMaker
        
        async def execute_select(self, statement):
            async with asyncSessionMaker() as session:
                rows = await session.execute(statement)
                return (
                    self.registerResult(row)
                    for row in rows.scalars()
                )
            
        async def filter_by(self, **filters):
            statement = mainstmt.filter_by(**filters)
            return await self.execute_select(statement)

        async def page(self, skip=0, limit=10, where=None, extendedfilter=None):
            statement = mainstmt
            if where is not None:
                statement = prepareSelect(dbModel, where)
            statement = statement.offset(skip).limit(limit)
            if extendedfilter is not None:
                statement = statement.filter_by(**extendedfilter)
            logging.info(f"loader.page statement {statement}")
            return await self.execute_select(statement)
            
        def set_cache(self, cache_object):
            self.cache = True
            self._cache = cache_object

    return Loader(cache=True)

class Loaders:
    users = None
    groups = None
    memberships = None
    grouptypes = None
    roles = None
    roletypes = None
    rolecategories = None
    pass

async def _createLoaders(
    asyncSessionMaker,
    DBModels=[
        UserModel,
        MembershipModel,
        GroupModel,
        GroupTypeModel,
        RoleModel,
        RoleTypeModel,
        RoleCategoryModel,
    ],
):

    modelIndex = dict((DBModel.__tablename__, DBModel) for DBModel in DBModels)

    result = {}
    for tableName, DBModel in modelIndex.items():  # iterate over all models
        result[tableName] = createIdLoader(asyncSessionMaker, DBModel)
    # result['memberships'].max_batch_size = 20
    return result

dbmodels = {
    "users": UserModel,
    "memberships": MembershipModel,
    "groups": GroupModel,
    "grouptypes": GroupTypeModel,
    "roles": RoleModel,
    "roletypes": RoleTypeModel,
    "rolecategories": RoleCategoryModel,
}

def createLoaders(asyncSessionMaker, models=dbmodels) -> Loaders:
    def createLambda(loaderName, DBModel):
        return lambda self: createIdLoader(asyncSessionMaker, DBModel)
    
    attrs = {}
    for key, DBModel in models.items():
        attrs[key] = property(cache(createLambda(key, DBModel)))
    
    Loaders = type('Loaders', (), attrs)   
    return Loaders()

from functools import cache

# async def createLoaders_2(
#     asyncSessionMaker,
#     DBModels = [UserModel, MembershipModel, GroupModel, GroupTypeModel, RoleModel, RoleTypeModel],
#     FKeyedDBModels = {}
#     ):

#     def IdLoader(DBModel):
#         @property
#         @cache
#         def getIt(self):
#             return createIdLoader(asyncSessionMaker, DBModel)

#     def keyedLoader(DBModel, foreignKeyName):
#         @property
#         @cache
#         def getIt(self):
#             return createFkeyLoader(asyncSessionMaker, DBModel, foreignKeyName=foreignKeyName)


#     modelIndex = dict((DBModel.__tablename__, DBModel) for DBModel in DBModels)
#     revIndex = dict((DBModel, DBModel.__tablename__) for DBModel in DBModels)

#     attrs = {}
#     for tableName, DBModel in modelIndex.items():  # iterate over all models
#         attrs[tableName] = IdLoader(DBModel)

#     for DBModel, fkeyNames in FKeyedDBModels.items():
#         tableName = revIndex[DBModel]
#         for fkeyName in fkeyNames:
#             name = tableName + '_' + fkeyName
#             attrs[name] = keyedLoader(DBModel, fkeyName)

#     result = type("loaders", (object, ), attrs)
#     #result = type("resolvers", (object, ), {'experiment': experiment, 'loader_a': experiment})
#     return result()


async def createLoaders_3(asyncSessionMaker):
    class Loaders:
        @property
        @cache
        def users(self):
            return createIdLoader(asyncSessionMaker, UserModel)

        @property
        @cache
        def groups(self):
            return createIdLoader(asyncSessionMaker, GroupModel)

        @property
        @cache
        def roles(self):
            return createIdLoader(asyncSessionMaker, RoleModel)

        @property
        @cache
        def roles_for_user_id(self):
            return createFkeyLoader(asyncSessionMaker, RoleModel, foreignKeyName="user_id")

        @property
        @cache
        def roletypes(self):
            return createIdLoader(asyncSessionMaker, RoleTypeModel)

        @property
        @cache
        def grouptypes(self):
            return createIdLoader(asyncSessionMaker, GroupTypeModel)

        @property
        @cache
        def memberships(self):
            return createIdLoader(asyncSessionMaker, MembershipModel)

        @property
        @cache
        def memberships_user_id(self):
            return createFkeyLoader(
                asyncSessionMaker, MembershipModel, foreignKeyName="user_id"
            )

        @property
        @cache
        def memberships_group_id(self):
            return createFkeyLoader(
                asyncSessionMaker, MembershipModel, foreignKeyName="group_id"
            )

        @property
        @cache
        def groups_mastergroup_id(self):
            return createFkeyLoader(
                asyncSessionMaker, GroupModel, foreignKeyName="mastergroup_id"
            )

    return Loaders()
