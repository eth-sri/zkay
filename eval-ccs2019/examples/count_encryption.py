# Convenience script for counting the number of enc/dec calls in the generated
# circuits.

import os
import pandas as pd
from glob import iglob

script_dir = os.path.dirname(os.path.realpath(__file__))

# create table
df = pd.DataFrame(columns=['filename', 'enc', 'dec']).set_index(['filename'])

pattern = os.path.join(script_dir, '**', 'Verify_*.code')
for filename in iglob(pattern, recursive=True):
	# get relative filename
	relative_filename = os.path.relpath(filename, script_dir)
	# count occurrences
	with open(filename, 'r') as f:
		content = f.read()
		n_enc = content.count('enc(') - 1
		n_dec = content.count('dec(') - 1
	# append information to table
	df.loc[relative_filename] = [n_enc, n_dec]

# compute total
df['total'] = df['enc'] + df['dec']

# print results
print(df)
print(df.agg(['mean', 'max']))