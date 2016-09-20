#!/usr/bin/env python


import json

from bottle import get, run, request, response, static_file
from py2neo import Graph


#password = {Your neo4j password}

graph = Graph(password = "graphdb", host = "graphdb")


@get("/")
def get_index():
    return static_file("index.html", root="static")


@get("/graph")
def get_graph():
    results = graph.run(
        "MATCH (m:Movie)<-[:ACTED_IN]-(a:Person) "
        "RETURN m.title as movie, collect(a.name) as cast "
        "LIMIT {limit}", {"limit": 100})
    nodes = []
    rels = []
    i = 0
    for movie, cast in results:
        nodes.append({"title": movie, "label": "movie"})
        target = i
        i += 1
        for name in cast:
            actor = {"title": name, "label": "actor"}
            try:
                source = nodes.index(actor)
            except ValueError:
                nodes.append(actor)
                source = i
                i += 1
            rels.append({"source": source, "target": target})
    return {"nodes": nodes, "links": rels}


@get("/search")
def get_search():
    try:
        q = request.query["q"]
    except KeyError:
        return []
    else:
        results = graph.run(
            "MATCH (movie:Movie) "
            "WHERE movie.title =~ {title} "
            "RETURN movie", {"title": "(?i).*" + q + ".*"})
        response.content_type = "application/json"
        return json.dumps([{"movie": dict(row["movie"])} for row in results])


@get("/movie/<title>")
def get_movie(title):
    results = graph.run(
        "MATCH (movie:Movie {title:{title}}) "
        "OPTIONAL MATCH (movie)<-[r]-(person:Person) "
        "RETURN movie.title as title,"
        "collect([person.name, head(split(lower(type(r)),'_')), r.roles]) as cast "
        "LIMIT 1", {"title": title})
    row = results.next()
    return {"title": row["title"],
            "cast": [dict(zip(("name", "job", "role"), member)) for member in row["cast"]]}


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
