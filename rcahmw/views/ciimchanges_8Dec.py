
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
        max_resourceid = request.GET.get("maxResourceId")
        per_page = int(request.GET.get("perPage"))

        # format the date times
        from_date = datetime.strptime(from_date, "%d-%m-%YT%H:%M:%SZ")
        to_date = datetime.strptime(to_date, "%d-%m-%YT%H:%M:%SZ")
        if not max_resourceid:
            max_resourceid = "0"
        if max_resourceid:
            max_resourceid = f'"{max_resourceid}"'

        build_results = True
        id_list = []
        dbQuery_start = time.perf_counter()
        loops = 0
        while build_results:
            loops += 1
            db_query = '''SELECT resourceinstanceid, timestamp
                        FROM edit_log WHERE timestamp >= (%s) AND timestamp <= (%s) AND resourceinstanceid > (%s)
                        ORDER BY resourceinstanceid, timestamp DESC LIMIT (2000)'''

            cur.execute(db_query, ([from_date, to_date, max_resourceid]))
 #           print("!!!!!!!!!!!!!!!!!!", cur.rowcount)
            #if cur.rowcount != 0:
            rows = cur.fetchall()
#            else               rows = []
#            print("!!!!!!!!!!!!!!!!!!!!!")
            query_result_list = list(set([i[0] for i in rows]))
#            print(loops)
 #           print(query_result_list)
#            df = pd.DataFrame(rows, columns=['resourceinstanceid', 'timestamp'])
 #           df = df.drop_duplicates(subset="resourceinstanceid")
  #          query_result_list = list(df['resourceinstanceid'])

            if query_result_list:
#                print("Query set triggered")
                id_list.extend(query_result_list)
                id_list = list(set(id_list))

                if max_resourceid == id_list[-1]:
                    build_results = False
                    max_resourceid = None

                # If we don't yet have {per_page} number of results
                # set max_id to the last in the list and run the loop again
                if len(id_list) < per_page:
                    max_resourceid = id_list[-1]

                # If we have more or equal to {per_page} number of results
                # Then take 0:{per_page}, set max_id to the last in the lsit
		# and stop the loop
                if len(id_list) >= per_page:
                    build_results = False
                    id_list = id_list[0:per_page]
                    max_resourceid = id_list[-1]
            else:
                build_results = False #if len(id_list) > 0:
                max_resourceid = None
        print(max_resourceid)
        if max_resourceid == "0":
            max_reourceid= None

        dbQuery_end =  time.perf_counter()

        dataProcessing_start = time.perf_counter()

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
        #df = df.sort_values(by=by, ascending=ascending)
        # format resultant resource ids into a list, drop and duplicates
        dataProcessing_end = time.perf_counter()

        dataDownload_start = time.perf_counter()
        resourceinstanceids = id_list
        results = []
        if settings.SYSTEM_SETTINGS_RESOURCE_ID in resourceinstanceids:
            resourceinstanceids.remove(settings.SYSTEM_SETTINGS_RESOURCE_ID)
        for resourceid in resourceinstanceids:
            try:
                resource = Resource.objects.get(pk=resourceid)
                resource.load_tiles()
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
            'maxResourceId':max_resourceid,
            'perPage':per_page,
            'numberLoops': loops,
            'timeElapsed':{
                'total':(end_time - start_time),
                'dbQuery': (dbQuery_end - dbQuery_start),
                'dataProcessing': (dataProcessing_end - dataProcessing_start),
                'dataDownload': (dataDownload_end - dataDownload_start)}
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





