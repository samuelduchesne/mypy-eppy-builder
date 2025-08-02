from archetypal.idfclass import IDF

idf = IDF()
obj = idf.newidfobject("SITE:LOCATIONS")  # <- deliberately incorrect class name; should raise pyright error
obj.Time_Zone = 1

for a in idf.idfobjects["SITE:LOCATIONS"]:  # <- deliberately incorrect class name; should raise pyright error
    print(a)
