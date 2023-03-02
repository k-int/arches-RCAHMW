import uuid
from datetime import datetime
import math
from arches.app.models.system_settings import settings
import time
import pandas as pd
import requests
import psycopg2
from django.views.generic import View
from django.http import JsonResponse, HttpResponse
from arches.app.models.concept import Concept
from arches.app.models.resource import Resource
from arches.app.utils.betterJSONSerializer import JSONSerializer
from arches.app.utils.skos import SKOSWriter, SKOSReader

# db connection - I should import this from settings.py
con = psycopg2.connect(database="rcahmw", user="postgres", password="postgis", host="localhost", port="5432")
cur = con.cursor()

class ChangesView(View):
    def get(self, request):
        start_time = time.perf_counter()
        # Grab the data from the request
        from_date =  request.GET.get("from")
        to_date = request.GET.get("to")
        sortField = request.GET.get("sortField")
        sortOrder = request.GET.get("sortOrder")
        offset = int(request.GET.get("offset"))
        _max = int(request.GET.get("max"))
        # format the date times
        from_date = datetime.strptime(from_date, "%d-%m-%YT%H:%M:%SZ")
        to_date = datetime.strptime(to_date, "%d-%m-%YT%H:%M:%SZ")

        dbQuery_start = time.perf_counter()

        db_query = '''SELECT resourceinstanceid, timestamp
                        FROM edit_log WHERE timestamp >= (%s) AND timestamp <= (%s)
                        ORDER BY timestamp DESC LIMIT (20000)'''

        # execute the query with dates from the request
        cur.execute(db_query, ([from_date, to_date]))
        # execute the query with dates from the request
        rows = cur.fetchall()
        dbQuery_end =  time.perf_counter()

        dataProcessing_start = time.perf_counter()

        # Load data into a python table
        df = pd.DataFrame(rows, columns=['resourceinstanceid', 'timestamp'])
#        df = pd.DataFrame(rows, columns=['resourceinstanceid', 'timestamp'])
        df = df.drop_duplicates(subset="resourceinstanceid")
        df = df[offset*_max: (offset*_max)+_max]
        debug_ids = list(df['resourceinstanceid'])
        # Grab the count from the db response (if empty set to 0)
#        count =400000 # int(df['count'][0]) if not df.empty else 0
        # set by variable based on sortField value
        if sortField in ['id','uuid', 'resourceinstanceid']:
            by = ['resourceinstanceid']
        if sortField in ['time', 'date', 'timestamp']:
            by = ['timestamp']
        # set variable ascending based on sortOrder value
        if sortOrder == 'asc':
            ascending = True
        if sortOrder == 'desc':
            ascending == False
        # use by and ascending to sort the results
        df = df.sort_values(by=by, ascending=ascending)
        # format resultant resource ids into a list, drop and duplicates
        resourceinstanceids = list(df['resourceinstanceid'].drop_duplicates())
        dataProcessing_end = time.perf_counter()

        dataDownload_start = time.perf_counter()
        results = []
        if settings.SYSTEM_SETTINGS_RESOURCE_ID in resourceinstanceids:
            resourceinstanceids.remove(settings.SYSTEM_SETTINGS_RESOURCE_ID)
        for resourceid in resourceinstanceids:
            try:
                resource = Resource.objects.get(pk=resourceid)
                resource.load_tiles() # user=request.user, perm="read_nodegroup")
                resource_json = JSONSerializer().serializeToPython(resource)
                if resource_json["displaydescription"] == "<Description>":
                    resource_json["displaydescription"] = None
                if resource_json["map_popup"] == "<Name_Type>":
                    resource_json["map_popup"] = None
                if resource_json["displayname"] == "<NMRW_Name>":
                    resource_json["displayname"] = None
                if len(resource.tiles) == 1 and not resource.tiles[0].data:
                    pass
                    # do nothing
                else:
                    results.append(resource_json) # user=request.user, perm="read_nodegroup")
            # Id no longer exsists.
            except:
                results.append({'resourceinstance_id':resourceid, 'tiles':None})
        dataDownload_end = time.perf_counter()

        end_time = time.perf_counter()
        metadata = {
            'from':from_date,
            'to':to_date,
            'sortField':sortField,
            'sortOrder':sortOrder,
            'offset':offset,
            'max':_max,
#            'totalHits':count,
#            'pages': math.ceil(count/_max),
            'timeElapsed':{
                'total':(end_time - start_time),
                'dbQuery': (dbQuery_end - dbQuery_start),
                'dataProcessing': (dataProcessing_end - dataProcessing_start),
                'dataDownload': (dataDownload_end - dataDownload_start)},
            'debug_ids':debug_ids
        }
        response = {'metadata': metadata, 'results': results}
        return JsonResponse(response, json_dumps_params={'indent': 2})

# download and append all xml thesauri
class ConceptsExportView(View):
    def get(self, request):
        cur.execute("SELECT * from concepts WHERE nodetype='ConceptScheme'")
        rows = set(cur.fetchall())
        conceptids = [row[0] for row in rows]
        concept_graphs = []
        for conceptid in conceptids:
            print(conceptid)
            concept_graphs.append(Concept().get(
                id=conceptid,
                include_subconcepts=True,
                include_parentconcepts=False,
                include_relatedconcepts=True,
                depth_limit=None,
                up_depth_limit=None))
        return HttpResponse(SKOSWriter().write(concept_graphs, format="pretty-xml"), content_type="application/xml")
