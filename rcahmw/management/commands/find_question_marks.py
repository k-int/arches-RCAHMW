from arches.app.models.tile import Tile
from arches.app.models.models import TileModel, ResourceInstance
from django.core.management.base import BaseCommand, CommandError
import json
import pandas as pd

class Command(BaseCommand):
    """
    Commands for managing datatypes
    """
    def handle(self, *args, **options):
        print("Running command...")
        tiles = Tile.objects.filter(nodegroup_id="60120f4c-9ff2-11ea-a530-000d3a86d704")
        j=0
        resids=[]
        for tile in tiles:
            if "60120f4c-9ff2-11ea-a530-000d3a86d704" in tile.data:
                if tile.data['60120f4c-9ff2-11ea-a530-000d3a86d704']:
                    if "?" in  tile.data['60120f4c-9ff2-11ea-a530-000d3a86d704']:
                        print(tile.resourceinstance_id)
                        j+=1
                        resids.append(str(tile.resourceinstance_id))
        print(j)
        df = pd.DataFrame({"ids":resids})
        df.to_csv("questionmarks_resourceids.csv")
