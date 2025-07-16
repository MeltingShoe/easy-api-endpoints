import os
import json
print(json.dumps({"available_endpoints":list(map(lambda x: x.split('.')[0], os.listdir('endpoints')))}))