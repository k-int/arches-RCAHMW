import uuid
from django.core.exceptions import ValidationError
from arches.app.models.tile import Tile, TileValidationError
from arches.app.functions.base import BaseFunction
from arches.app.models import models
from arches.app.models.tile import Tile
import json
import logging
logger = logging.getLogger(__name__)

details = {
    "name": "Required-Node Function",
    "type": "node",
    "description": "Just a sample demonstrating node group selection",
    "defaultconfig": {"selected_nodegroup": "", "target_node":""},
    "classname": "RequiredNode",
    "component": "views/components/functions/required_node",
}


class RequiredNode(BaseFunction):
    def post_save(self, tile, request):
        logger.warning("CALLING REQUIRED NODE FN")
        tile_already_exists = models.TileModel.objects.filter(resourceinstance_id=tile.resourceinstance_id).filter(nodegroup_id=self.config["selected_nodegroup"]).exists()
        if not tile_already_exists:
            raise TileValidationError("Error! You must first assign a NPRN to this record.")
