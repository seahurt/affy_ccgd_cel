# affy_ccgd_cel
Read COMMAND CONSOLE GENERIC DATA FILE

# File format description

```
https://www.affymetrix.com/support/developer/powertools/changelog/gcos-agcc/generic.html
https://www.affymetrix.com/support/developer/powertools/changelog/gcos-agcc/cel.html
```

# Usage
```
from cel_file import CelFile
import json

cf = CelFile(file_path)  # automatic read file header, general data header, parent data header, extra header
cf.read_data_groups()  # data groups was stored in self.data_groups
print(cf.array_id)
print(cf.barcode)

print(cf.parameters_table(cf.header['parameters']))

with open('data_group.json', 'w') as f:
    json.dump(cf.data_groups, f, indent=4)
```

# extra header
```
extra header was not listed in the affy web page, but I found those bytes lie in my test cel files.
```

# Tested Platform
```
CytoScan 750K Assay
```

