
class Paths:
    """Given a bunch of short paths (or just segments) and flashes, tries to
    join paths together."""

    def __init__(self):
        super().__init__()
        self._endps = {}

    def _pop_path(self, coord, suffix):
        path = self._endps.get(coord, None)
        if path is None:
            return [coord]
        self._endps.pop(path[0], None)
        self._endps.pop(path[-1], None)
        return path

    def add(self, *path):
        path = list(path)
        assert len(path) >= 1
        if len(path) == 1:
            if path[0] not in self._endps:
                self._endps[path[0]] = path
            return

        prefix = self._pop_path(path[0], False)
        if prefix[-1] != path[0]:
            prefix.reverse()
        assert prefix[-1] == path[0]

        suffix = self._pop_path(path[-1], True)
        if suffix[0] != path[-1]:
            suffix.reverse()
        assert suffix[0] == path[-1]

        path = prefix + path[1:-1] + suffix

        self._endps[path[0]] = path
        self._endps[path[-1]] = path

    def __iter__(self):
        ids = set()
        for path in self._endps.values():
            if id(path) not in ids:
                ids.add(id(path))
                yield path
