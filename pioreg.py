def filter_field_ty(f):
  if test_enum(f):
    return filter_tyname(f)
  elif f.bitWidth == 1:
    return "bool"
  else:
    return "u{}".format(f.parent.size)

def test_enum(f):
  return len(filter_all_enums(f)) > 0

def filter_tyname(v):
  # naming rules:
  #   Peripheral is preerve-case (which is usually upper-case)
  #   Register is lower-case
  #   Field is lower-case
  if str(type(v).__name__) == "Peripheral":
    return v.name
  elif str(type(v).__name__) == "Register":
    return "{}_{}".format(filter_tyname(v.parent), v.name.lower())
  elif str(type(v).__name__) == "Field":
    return "{}_{}".format(filter_tyname(v.parent), v.name.lower())
  else:
    raise RuntimeError("Unknown type for name: {}".format(str(type(v))))

def filter_validate_register(r):
  if r.size != 32:
    raise RuntimeError("Unsupported register size: {}".format(r.size))
  return ''

def filter_sanitize_name(n):
  n = n.lower()
  BAD_NAMES = ("match",)
  if n in BAD_NAMES:
    return n + "_"
  else:
    return n

def filter_accessible_fields(r):
  return [f for f in r.fields if f.name not in cache.ignored_fields()]

def filter_enum_fields(r):
  return [f for f in r.fields if test_enum(f)]

def filter_accessible_enums(f):
  # TODO(farcaller): f.enumeratedValues split is strange
  return [e for e in filter_all_enums(f) if e.name not in cache.ignored_enums()]

def filter_all_enums(f):
  enums = []
  for enums_list in f.enumeratedValues.values():
    for e in enums_list:
      enums.append(e)
  return enums

def filter_sanitize_enum(n):
  return cache.get_enum(n)

class NameCache(object):
  def __init__(self):
    from yaml import load
    try:
      from yaml import CLoader as Loader
    except ImportError:
      from yaml import Loader

    text = open("names.yml").read()
    self.data = load(text, Loader=Loader)
    self.badnames = []

  def get_enum(self, name):
    rename = self.data["rename"]
    if name in rename:
      v = rename[name]
      if type(v) == str or type(v) == unicode:
        return v
      else:
        return v.pop(0)
    else:
      if name not in self.badnames:
        self.badnames.append(name)
        print "Enum name not provided: {}".format(name)
      return name

  def ignored_fields(self):
    return self.data.get("ignored_fields", [])

  def ignored_enums(self):
    return self.data.get("ignored_enums", [])

  def remove_fields(self):
    return self.data.get("remove_fields", [])

  def rename_enums(self):
    return self.data.get("rename_enums", [])

cache = NameCache()

def preprocess_remove_bad_regs(vardict):
  toremove = cache.remove_fields()
  for k in toremove:
    pn, rn, fn = map(lambda x:x.lower(), k.split("."))
    p = [p for p in vardict["peripherals"] if p.name.lower() == pn][0]
    r = [r for r in p.registers if r.name.lower() == rn][0]
    f = [f for f in r.fields if f.name.lower() == fn][0]
    r.fields.remove(f)
  return vardict

def preprocess_rename_enums(vardict):
  torename = cache.rename_enums()
  for k, new_name in torename.iteritems():
    pn, rn, fn, idx = map(lambda x:x.lower(), k.split("."))
    idx = int(idx)
    p = [p for p in vardict["peripherals"] if p.name.lower() == pn][0]
    r = [r for r in p.registers if r.name.lower() == rn][0]
    f = [f for f in r.fields if f.name.lower() == fn][0]
    e = f.enumeratedValues[f.access]

    e[idx].name = new_name
  return vardict

def filter_mask(v):
  return (1 << v) - 1
