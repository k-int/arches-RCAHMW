import uuid
from datetime import datetime
import math
from arches.app.models.system_settings import settings
import time
import requests
import psycopg2
from django.views.generic import View
from django.http import JsonResponse, HttpResponse
from arches.app.models.concept import Concept
from arches.app.models.resource import Resource
from arches.app.models.models import Concept as modelsConcept
from arches.app.utils.betterJSONSerializer import JSONSerializer
from arches.app.utils.skos import SKOSWriter, SKOSReader
from arches.app.models.models import LatestResourceEdit

con = psycopg2.connect(database="rcahmw", user="postgres", password="postgis", host="localhost", port="5432")
cur = con.cursor()

class ChangesView(View):
    def get(self, request):
        start_time = time.perf_counter()
        from_date =  request.GET.get("from")
        to_date = request.GET.get("to")
        per_page = int(request.GET.get("perPage"))
        page=int(request.GET.get("page"))
        if page < 1:
            raise Exception("Pagination starts at page=1")
        # format the date times
        from_date = datetime.strptime(from_date, "%d-%m-%YT%H:%M:%SZ")
        to_date = datetime.strptime(to_date, "%d-%m-%YT%H:%M:%SZ")

        dbQuery_start = time.perf_counter()

        edits = LatestResourceEdit.objects.filter(timestamp__range=(from_date, to_date)).order_by('timestamp')

        resource_ids = [edit.resourceinstanceid for edit in edits]
        no_pages = int(math.ceil(len(resource_ids)/per_page))
        resourceinstanceids = resource_ids[(page-1)*per_page:page*per_page]

        dbQuery_end =  time.perf_counter()

        dataDownload_start = time.perf_counter()
        #resourceinstanceids = id_list
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
            except:
                results.append({'resourceinstance_id':resourceid, 'tiles':None})
        dataDownload_end = time.perf_counter()

        end_time = time.perf_counter()
        metadata = {
            'from':from_date,
            'to':to_date,
            'totalNumberOfResources':len(resource_ids),
            'perPage':per_page,
            'page': page,
            'numberOfPages':no_pages,
            'timeElapsed':{
                'total':(end_time - start_time),
                'dbQuery': (dbQuery_end - dbQuery_start),
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
            concept_graphs.append(Concept().get(
                id=conceptid,
                include_subconcepts=True,
                include_parentconcepts=False,
                include_relatedconcepts=True,
                depth_limit=None,
                up_depth_limit=None))
        return HttpResponse(SKOSWriter().write(concept_graphs, format="pretty-xml"), content_type="application/xml")
