#!/usr/bin/env python


import json

from bottle import get, run, request, response, static_file
from py2neo import Graph

graph = Graph(password = "graphdb", host = "graphdb")


# Allowed ABFs for a given API or API to ABF relationship.
#curl -XGET http://localhost:8080/authz/APIs/API1
@get("/authz/APIs/<api>")
def get_abf(api):
    results = graph.run(
        "MATCH  (api:API) - [r:INVOKED_BY] -> (abf:ABF) "
        "WHERE api.API =~ {api} "
        "RETURN abf.ABFName as ABFName", {"api": api})
    print (results)
    response.content_type = "application/json"
    #return results

    return json.dumps([{"ABFName": row} for row in results])

# Customer Entitlements
#curl -XGET http://localhost:8080/authz/customerentitlements/5/FAN000008
@get("/authz/customerentitlements/<custid>/<fan>")
def get_cust_abf(custid,fan):
    
    results = graph.run(
        "MATCH (c:Customer) - [lnk:ASSOCIATED_TO] -> (a: Account) - [stat: BELONG_TO] -> (as:AccountStatus) <- [access:ACCESSING] - (cr: CustomerRole) "
        "WHERE lnk.Role = cr.Description and c.CustomerID = {custid} and a.FAN = {fan} "
        "RETURN DISTINCT access.AllowedABFs as ABFName", {"custid":custid, "fan":fan}) 
    print (results)
    response.content_type = "application/json"
    return json.dumps({"Entitlements": row for row in results})

# Customer Accessing a specific API, if ABFs are returned for a given API and customerid and FAN, i.e. customer is allowed to access given API based on returned ABFs.
#curl -XGET http://localhost:8080/authz/apienforcement/API1/5/FAN000008
@get("/authz/apienforcement/<api>/<custid>/<fan>")
def get_cust_abf(api,custid,fan):
    
    results = graph.run(
        "MATCH (c:Customer) - [lnk:ASSOCIATED_TO] -> (a: Account) - [stat: BELONG_TO] -> (as:AccountStatus) <- [access:ACCESSING] - (cr: CustomerRole) "
        "MATCH (abf: ABF) <- [rel: INVOKED_BY] - (api:API) "
        "where lnk.Role = cr.Description and c.CustomerID = {custid} and a.FAN = {fan} and api.API = {api} "
        "and abf.ABFName in access.AllowedABFs "
        "return DISTINCT abf.ABFName as ABFName", {"api":api, "custid":custid, "fan":fan})
    print (results)
    response.content_type = "application/json"
    return json.dumps([{"AllowedABFs": row} for row in results])



if __name__ == "__main__":
    run(port=8080)
