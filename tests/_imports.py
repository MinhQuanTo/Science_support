import types

import gql_ug

GraphTypeDefinitions: types.ModuleType = gql_ug.GraphTypeDefinitions
DBDefinitions: types.ModuleType = gql_ug.DBDefinitions
Dataloaders: types.ModuleType = gql_ug.Dataloaders
DBFeeder: types.ModuleType = gql_ug.DBFeeder

schema = GraphTypeDefinitions.schema