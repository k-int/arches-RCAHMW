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
        tiles = Tile.objects.filter(nodegroup_id="60120f5e-9ff2-11ea-a530-000d3a86d704")
        print(len(tiles))
        for tile in tiles:
            if not tile.data['60120f5e-9ff2-11ea-a530-000d3a86d704']:
                print(tile.resourceinstance_id)
                print(tile.data)
