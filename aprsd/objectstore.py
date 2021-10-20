import logging
import os
import pathlib
import pickle

from aprsd import config as aprsd_config


LOG = logging.getLogger("APRSD")


class ObjectStoreMixin:
    """Class 'MIXIN' intended to save/load object data.

    The asumption of how this mixin is used:
      The using class has to have a:
         * data in self.data as a dictionary
         * a self.lock thread lock
         * Class must specify self.save_file as the location.


    When APRSD quits, it calls save()
    When APRSD Starts, it calls load()
    aprsd server -f (flush) will wipe all saved objects.
    """

    def __len__(self):
        return len(self.data)

    def get_all(self):
        with self.lock:
            return self.data

    def get(self, id):
        with self.lock:
            return self.data[id]

    def _save_filename(self):
        return "{}/{}.p".format(
            aprsd_config.DEFAULT_CONFIG_DIR,
            self.__class__.__name__.lower(),
        )

    def _dump(self):
        dump = {}
        with self.lock:
            for key in self.data.keys():
                dump[key] = self.data[key]

        LOG.debug(f"{self.__class__.__name__}:: DUMP")
        LOG.debug(dump)

        return dump

    def save(self):
        """Save any queued to disk?"""
        if len(self) > 0:
            LOG.info(f"{self.__class__.__name__}::Saving {len(self)} entries to disk")
            pickle.dump(self._dump(), open(self._save_filename(), "wb+"))
        else:
            LOG.debug(
                "{} Nothing to save, flushing old save file '{}'".format(
                    self.__class__.__name__,
                    self._save_filename(),
                ),
            )
            self.flush()

    def load(self):
        if os.path.exists(self._save_filename()):
            raw = pickle.load(open(self._save_filename(), "rb"))
            if raw:
                self.data = raw
                LOG.debug(f"{self.__class__.__name__}::Loaded {len(self)} entries from disk.")
                LOG.debug(f"{self.data}")

    def flush(self):
        """Nuke the old pickle file that stored the old results from last aprsd run."""
        if os.path.exists(self._save_filename()):
            pathlib.Path(self._save_filename()).unlink()
        with self.lock:
            self.data = {}
