from arches.app.models.tile import Tile
from arches.app.models.models import TileModel, ResourceInstance
from django.core.management.base import BaseCommand, CommandError
import json

class Command(BaseCommand):
    """
    Commands for managing datatypes
    """
    def handle(self, *args, **options):
        print("Running command...")
        resourceinstances = ResourceInstance.objects.all()
        resourceinstance_ids = [str(res.resourceinstanceid) for res in resourceinstances]
        nprn_node = "60120f4f-9ff2-11ea-a530-000d3a86d704"
        for res in resourceinstance_ids:
            if res != "a106c400-260c-11e7-a604-14109fd34195":
                tiles = TileModel.objects.filter(resourceinstance_id=res).all()
                if not tiles.filter(nodegroup_id=nprn_node):
                    print(res)
