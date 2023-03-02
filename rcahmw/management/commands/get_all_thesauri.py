#Imports
import os
from django.core.management.base import BaseCommand, CommandError

from arches.app.utils.skos import SKOSWriter

#Models
from arches.app.models.models import Concept as modelConcept
from arches.app.models.concept import Concept

class Command(BaseCommand):
    '''
    Command for downloading all thresauri as indvidual files
    '''

    def handle (self, *args, **options):
        #Get id's of all thesauris
        concept_ids = [str(concept.conceptid) for concept in modelConcept.objects.filter(nodetype='ConceptScheme')]

        for concept_id in concept_ids:
            #Create a thesauri file in the root directory of the project
            file = open(os.path.abspath(f"./concepts/{concept_id}.xml"), 'wb')

            #Get the thesauri
            concept = Concept().get(
                id = concept_id,
                include_subconcepts=True,
                include_parentconcepts=False,
                include_relatedconcepts=True,
                depth_limit=None,
                up_depth_limit=None
                ) 

            #Write the thesauri to file
            file.write(SKOSWriter().write(concept, format="pretty-xml"))
            file.close()
