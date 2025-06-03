from unittest import TestCase

from operations import CacheUpdate

TESTING_ROOTLDIR_ID = "f3f79de4-0895-43e5-81ef-9ae91b19254c"


class TestCacheUpdate(TestCase):

    def test_run_some(self):
        update = CacheUpdate()
        update.update(TESTING_ROOTLDIR_ID)

        self.assertIsNotNone(update.cache.get_directory_path(TESTING_ROOTLDIR_ID))

