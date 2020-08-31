import collections
import re

class MustHave:
    def __init__(self, *reqs):
        self.requirements = list(reqs)

    def append(self, req):
        self.requirements.append(req)

    def extend(self, reqs):
        self.requirements.extend(reqs)

    def descriptions(self):
        for r in self.requirements:
            yield r.description()

    def check(self, table):
        for r in self.requirements:
            yield r, r.check(table)

class columns_named:
    def __init__(self, colnames):
        self.colnames = colnames

    def description(self):
        desc = "Must have columns {0}."
        return desc.format(self.colnames)

    def check(self, t):
        missing = [c for c in self.colnames if c not in t]
        return must_have_result(missing=missing)

class columns_matching:
    def __init__(self, pattern):
        self.pattern = pattern

    def description(self):
        desc = "All columns must match pattern '{0}'."
        return desc.format(self.pattern)

    def check(self, t):
        not_matching = [
            c for c in t.colnames() if not matching(self.pattern, c)]
        return must_have_result(not_matching=not_matching)

class values_in_set:
    def __init__(self, colname, allowed):
        self.colname = colname
        self.allowed = allowed

    def description(self):
        desc = "Values of '{0}' must be in list: {1}."
        return desc.format(self.colname, self.allowed)

    def check(self, t):
        if self.colname not in t:
            return DoesntApply(self.colname)
        vals = t.get(self.colname)
        not_allowed = [v for v in vals if v not in self.allowed]
        return must_have_result(not_allowed=not_allowed)

class some_value_for:
    def __init__(self, *colnames):
        self.colnames = list(colnames)
        assert(len(self.colnames) >= 1)

    def description(self):
        if len(self.colnames) == 1:
            desc = "Values of '{0}' must not be missing or empty."
            return desc.format(self.colnames[0])
        elif len(self.colnames) == 2:
            desc = "Must have '{0}' filled in when '{1}' is filled in."
            return desc.format(self.colnames[1], self.colnames[0])
        else:
            desc = "Must have '{0}' filled in when {1} are filled in."
            return desc.format(self.colnames[-1], self.colnames[:-1])

    def check(self, t):
        missing = [c for c in self.colnames if c not in t]
        if missing:
            return DoesntApply(*missing)
        vals = zip(*(t.get(c) for c in self.colnames))
        idxs = [
            idx for idx, vs in enumerate(vals)
            if all(vs[:-1]) and (not vs[-1])]
        return must_have_result(idxs=idxs)

class values_matching:
    def __init__(self, colname, pattern):
        self.colname = colname
        self.pattern = pattern

    def description(self):
        desc = "Values of '{0}' must match pattern '{1}'."
        return desc.format(self.colname, self.pattern)

    def check(self, t):
        if self.colname not in t:
            return DoesntApply(self.colname)
        vals = t.get(self.colname)
        not_matching = [v for v in vals if not matching(self.pattern, v)]
        return must_have_result(not_matching=not_matching)

class unique_values_for:
    def __init__(self, *colnames):
        self.colnames = list(colnames)
        assert(len(self.colnames) >= 1)

    def description(self):
        if len(self.colnames) == 1:
            desc = "Values of '{0}' must be unique."
            return desc.format(self.colnames[0])
        else:
            desc = "Values of {0} must be unique together."
            return desc.format(self.colnames)

    def check(self, t):
        missing = [c for c in self.colnames if c not in t]
        if missing:
            return DoesntApply(*missing)
        vals = zip(*(t.get(c) for c in self.colnames))
        vals = [v for v in vals if any(v)]
        value_cts = collections.Counter(vals)
        repeated = [(v, n) for v, n in value_cts.items() if n > 1]
        return must_have_result(repeated=repeated)

def matching(pattern, x):
    return (x is None) or (re.search(pattern, x) is not None)

def must_have_result(**kwargs):
    problems = dict((k, v) for k, v in kwargs.items() if v)
    if not problems:
        return AllGood()
    else:
        return StillNeeds(**kwargs)

class AllGood:
    success = True

    def message(self):
        return "OK"

class DoesntApply:
    success = None

    def __init__(self, *colnames):
        assert(len(colnames) >= 1)
        self.colnames = colnames

    def message(self):
        if len(self.colnames) == 1:
            c = self.colnames[0]
            reason = "column {0} is missing".format(c)
        else:
            cs = ", ".join(self.colnames)
            reason = "columns {0} are missing".format(cs)
        return "Doesn't apply because {0}.".format(reason)

class StillNeeds():
    success = False

    def __init__(
            self, missing = None, idxs = None, not_matching = None,
            repeated = None, not_allowed = None):
        self.missing = missing
        self.idxs = idxs
        if self.idxs:
            self.idxs = [x + 1 for x in self.idxs]
        self.not_matching = not_matching
        self.repeated = repeated
        self.not_allowed = not_allowed

    def message(self):
        parts = [
            ("Missing: {0}", self.missing),
            ("In rows (starting from 1): {0}", self.idxs),
            ("Not matching: {0}", self.not_matching),
            ("Not allowed: {0}", self.not_allowed)
        ]
        lines = [t.format(a) for t, a in parts if a is not None]
        if self.repeated:
            rep_message = "{0} is repeated {1} times"
            reps = [rep_message.format(r, n) for r, n in self.repeated]
            lines.append("Repeated: {0}".format("; ".join(reps)))
        return "\n".join(lines)
