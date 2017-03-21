import json



class BackupSaver:
    def __init__(self, backup_file_name, house):
        
        self.file = backup_file_name
        
        self.house = house
    
    def save_backup(self):
        f = open(self.file, "w")
        
        data = self.house.get_info()
        areas = []
        for a in self.house.areas.values():
            a_rep = a.get_info()
            areas.append(a_rep)
            
            servers = []
            for s in a.servers.values():
                s_rep = s.get_info()
                s_rep["DIVISIONS"] = s.divisions.keys()
                servers.append(s_rep)
                
            divisions = []
            for d in a.divisions.values():
                divisions.append(d.get_info())
                
            a_rep["DIVISIONS"] = divisions
            a_rep["SERVERS"] = servers
        data["AREAS"] = areas
        
        print data
        json.dump({"HOUSE": data}, f)
        f.close()
        
        