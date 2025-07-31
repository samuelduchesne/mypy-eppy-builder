from archetypal.idfclass import IDF

idf = IDF(file_version="23.1")
obj = idf.newidfobject("SITE:LOCATION")
obj.Time_Zone = 1

for a in idf.idfobjects["SITE:LOCATION"]:
    print(a.Elevation)
