from unittest.mock import AsyncMock, MagicMock

import pytest

import stockx
from stockx.ext.inventory import ListedItem
from stockx.ext.inventory.batch.operations import update_quantity


