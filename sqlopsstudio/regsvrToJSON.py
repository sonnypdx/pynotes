# import necessary modules
import datetime
import random
import json
import re
import untangle
import uuid

from random import *

# Declare some constants
CONST_UriPfx = '/RegisteredServersStore/ServerGroup/DatabaseEngineServerGroup/ServerGroup/'
CONST_DbNameRegEx = 'initial catalog=(\w+);'
CONST_WinAuthRegEx = 'integrated security=True;'.lower()
CONST_GuidPfx = 'urn:uuid:'

#-- Start of getGroupName - Group of SQL Server Connections
def getGroupName(dbConnNd):
    parentUri = dbConnNd.RegisteredServers_Parent.sfc_Reference.sml_Uri.cdata
    return parentUri[len(CONST_UriPfx):]
#-- End of getGroupName

#-- Start of getDbName - find the database name
def getDbName(dbConnStr):
    m = re.search(CONST_DbNameRegEx, dbConnStr.lower())
    if m:
        return m.group(0)
    else:
        return ""
#-- End of getDbName

#-- Start of getAuthType - find the authentication type windows vs sql login
def getAuthType(dbConnStr):
    m = re.search(CONST_WinAuthRegEx, dbConnStr.lower())
    if m:
        return "Integrated"
    else:
        return "SqlLogin"
#-- End of getAuthType


#-- Start of getDbConnObj - SQL Server Connection node
def getDbConnObj(svrNd):
    if hasattr(svrNd.data, 'RegisteredServers_RegisteredServer'):
        result = {}

        svr = svrNd.data.RegisteredServers_RegisteredServer

        result["DatabaseDisplayName"] =  svr.RegisteredServers_Name.cdata
        result["Description"] =  svr.RegisteredServers_Name.cdata
        result["GroupName"] = getGroupName(svr)
        result["ServerName"] = svr.RegisteredServers_ServerName.cdata
        result["ServerType"] = svr.RegisteredServers_ServerType.cdata
        dbConnStr = svr.RegisteredServers_ConnectionStringWithEncryptedPassword.cdata
        result["Database"] = getDbName(dbConnStr)
        result["AuthenticationType"] = getAuthType(dbConnStr)
        return result
    else:
        return None
#-- End of getDbConnObj

#-- Start of getDictDbConns, create the dict of server connections
def getDictDbConns(docs):
    # create a dictionary to hold the groups and their corresponding server connections
    dictDbConns = dict()

    for doc in docs.document:
        dbCN = getDbConnObj(doc)
        if dbCN:
            grpName = dbCN["GroupName"]
            if not (dictDbConns.get(grpName)):
                dictDbConns[grpName] = []
            dictDbConns[grpName].append(dbCN)

    return dictDbConns
#-- End of getDictDbConns

#-- Start of getGuid, create a guid to be used with object instance in JSON
def getGuid():
    #return "guid_" + str(datetime.datetime.now())
    u = uuid.uuid4().urn
    return u[len(CONST_GuidPfx):]
#-- End of getGuid

#-- Start of getColor, get a random color for the group
def getColor():
    return '#{:06x}'.format(randint(0, 255**3))
#-- End of getColor

#-- Start of getConnGroup, Server Group for connections
def getConnGroup(name):
    grp = {}
    grp["name"] = name
    grp["id"] = getGuid()
    grp["parentId"] = "_fill_this_with_actual_parent_id_"
    grp["color"] = getColor()
    grp["description"] = "Connections for Group - " + name

    return grp
#-- End of getConnGroup

#-- Start of getDbConn, database connection
def getDbConn(cnObj, grpGuid):
    opts = {}
    opts["server"] = cnObj["ServerName"]
    opts["database"] = cnObj["Database"]
    opts["authenticationType"] = cnObj["AuthenticationType"]
    opts["user"] = ""
    opts["password"] = ""
    opts["applicationName"] = "sqlops"
    opts["databaseDisplayName"] = cnObj["DatabaseDisplayName"]

    result = {}
    result["options"] = opts
    result["groupId"] = grpGuid
    result["providerName"] = "MSSQL"
    result["savePassword"] = "false"
    result["id"] = getGuid()

    return result
#-- End of getDbConn

#-- Start of getDictSvrConns, create the dict of server connections
def convToSqlOpsStudioJSON(dictSvrs):
    connGrps = []
    dbConns = []

    for key in dictSvrs:
        # create the connection group
        grp = getConnGroup(key)
        connGrps.append(grp)

        for svr in dictSvrs[key]:
            dbCN = getDbConn(svr, grp["id"])
            dbConns.append(dbCN)

    result = {}
    result["datasource.connectionGroups"] = connGrps
    result["datasource.connections"] = dbConns

    return result
#-- End of getDictSvrConns

# Main program

regsvrFilename = 'sample.regsvr'
regsvrData = untangle.parse(regsvrFilename)
docs = regsvrData.model.xs_bufferSchema.definitions.document.data.xs_schema.RegisteredServers_bufferData.instances

dictDbConns = getDictDbConns(docs)
dictForSqlOpsConf = convToSqlOpsStudioJSON(dictDbConns)
jsonStr = json.dumps(dictForSqlOpsConf, indent = 4)
print(jsonStr)

# output to a file
with open("SqlOpsStudio.json", "w") as text_file:
    text_file.write(jsonStr)

print("\n--- Successfully Completed ---\n")
