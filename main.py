from hashlib import sha256
from collections import OrderedDict, defaultdict
from ordered_set import OrderedSet
from datetime import datetime
from operator import attrgetter
from pprint import pprint
import random
database = {}
def generate_hash(value):
  if type(value) == str:
    return value
  if type(value) == int:
    return str(value)
  if type(value) == dict:
    hash = ""
    for key, value in value.items():
      hash += key
      hash += generate_hash(value)
    return hash
    

def merge(a, b):
  for key, value in b.items():
    if key in a and type(a[key]) == dict and type(b[key]) == dict:
      merge(a[key], b[key])
    else:
      a[key] = b[key]

class MerkleClock:
  @classmethod
  def new_root(cls, database):
    
    hash = str(random.getrandbits(128)).encode("utf8")
    root_cid = sha256(hash).hexdigest()
    new_root = MerkleClock(root_cid, database, "", "", OrderedSet(), None, None)
    database[root_cid] = new_root
    return new_root



  def __init__(self, cid, database, key, value, children, previous, cache):
    self.cid = cid
    self.database = database
    self.value = value
    self.key = key
    self.children = children
    self.previous = previous
    self.timestamp = None
    if cache == None:
      self.cache = {}
    else:
      self.cache = cache

  def __eq__(self, item):
    if isinstance(item, MerkleClock) and item.cid == self.cid:
      return True
    else:
      return False

  def __hash__(self):
    return hash(self.cid)
  
  def __repr__(self):
    data = ""
    data = data + self.key + "{"
    for value in self.children:
      data += "{} = {} ".format(value.key, str(value.value))
    data += "}\n"
    return data
    
  def set(self, user, key, value, timestamp=None):
    if timestamp == None:
      timestamp = datetime.now()
    if type(value) == dict:
      last = MerkleClock.new_root(database)
      hash = ""
      last.user = user
      

      new_children = OrderedSet(self.children)
      cachevalues = {}
      for lkey, subvalue in value.items():
        
        last = last.set(user, lkey, subvalue, timestamp)
        cachevalues[lkey] = last
        
        

      
      
      new_cid = sha256((key + generate_hash(value)).encode("utf8")).hexdigest()
      new_keyvalue = last
      last.timestamp = timestamp
      last.key = key
      last.value = value
      new_children.add(last)
            
      

      new_cache = dict(self.cache)
      root_cid = sha256("".join([clock.cid for clock in new_children]).encode("utf8")).hexdigest()
      new_root = MerkleClock(root_cid, self.database, key, value, new_children, None, new_cache)
      new_root.timestamp = timestamp
      self.database[root_cid] = new_root
      self.database[new_cid] = new_keyvalue
      if key in new_root.cache:
        new_children.remove(self.cache[key])
        
      new_root.cache[key] = new_keyvalue

      for lkey, subvalue in value.items():
        new_root.cache[lkey] = cachevalues[lkey]
        
      new_root.user = user
      return new_root
    if type(value) == str or type(value) == int:
      new_children = OrderedSet(self.children)
      new_cid = sha256((key + str(value)).encode("utf8")).hexdigest()
      
      new_keyvalue = MerkleClock(new_cid, self.database, key, value, OrderedSet(), self, None)
      new_keyvalue.timestamp = timestamp
      new_keyvalue.user = user
      new_children.add(new_keyvalue)


      root_cid = sha256("".join([clock.cid for clock in new_children]).encode("utf8")).hexdigest()
      new_root = MerkleClock(root_cid, self.database, "", "", new_children, None, self.cache)
      self.database[root_cid] = new_root
      new_root.timestamp = timestamp
      new_root.user = user
      self.database[new_cid] = new_keyvalue
      if key in new_root.cache:
       new_children.remove(self.cache[key])
      new_root.cache[key] = new_keyvalue
      return new_root
      
  def lookup(self, key):
    return self.cache[key].inflate()

  def inflate(self):
    data = defaultdict(lambda:  defaultdict(defaultdict))
    
    
    for value in sorted(self.children, key=attrgetter("timestamp")):
      key = value.key
      
      if type(value.value) == dict and (type(data[self.key][key]) == dict or key not in data[self.key] or self.key not in data):
        merge(data[self.key][key], value.value)
      
        
        
      else:
        data[self.key][key] = value.value
      
    
    return data

  def wrap(self, new_children, source):
    new_cache = dict(source.cache)
    root_cid = sha256("".join([clock.cid for clock in new_children]).encode("utf8")).hexdigest()
    
    
    new_root = MerkleClock(root_cid, self.database, "root", "", new_children, None, new_cache)
    new_root.timestamp = max(new_children, key=attrgetter("timestamp")).timestamp
    return new_root, root_cid

  def rootmerge(self, clock, path=""):
    return self.merge(self.wrap([clock], clock)[0], path)
  
  def merge(self, clock, path=""):
    new_children = OrderedSet()
    
    
    for child in self.children:
      for merge_child in clock.children:
        
        if path + child.key == path + merge_child.key:
          
          if type(child.value) == dict and type(merge_child.value) == dict:
            merged = child.merge(merge_child, path + child.key)
            
            new_children.append(merged)
            
          
            
          else:
            
            if merge_child.timestamp > child.timestamp:
              new_children.add(merge_child)
            elif child.timestamp > merge_child.timestamp:
              new_children.add(child)
            elif merge_child.user > child.user:
              new_children.add(child)
            elif child.user > merge_child.user:
              new_children.add(merge_child)
        
          
          
       

    new_children |= clock.children
    new_children |= self.children

    
    

    
    
    new_root, root_cid = self.wrap(new_children, self)
    self.database[root_cid] = new_root
    
    return new_root
    


      
m1 = MerkleClock.new_root(database)
ma = m1.set(0, "one", "two")
m2 = ma.set(0, "hello", "world")
m3 = m2.set(0, "hello", "world2")
m4 = m3.set(0, "hello", {
  "hi": {"world": "6", "conflict": 1}
})


print(m4.lookup("hello"))

a1 = MerkleClock.new_root(database)
a2 = a1.set(1, "world", "hi")
am = a2.set(1, "three", "four")
a3 = am.set(1, "hello", {
  "hi": {"another": "7", "conflict": 0}
})
merged = m4.merge(a3)
print(database)


for child in merged.children:
  print("key")
  print(child.value)

data = dict(merged.inflate())
print("merge direction 1")
pprint(data)

print("other way merge")
merged2 = a3.merge(m4)

for child in merged2.children:
  print("key")
  print(child.key)

data2 = dict(merged2.inflate())
pprint(data2)

s1 = MerkleClock.new_root(database)
s2 = s1.set(1, "amazing", "yes")
s3 = s2.set(1, "three", "five")
s4 = s3.set(1, "hello", {
  "hi": {"another": "7", "conflict": 3}
})

print("Merge of root element")
merged3 = merged2.merge(s4)
data3 = dict(merged3.inflate())
pprint(data3)