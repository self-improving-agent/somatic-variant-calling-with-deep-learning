import numpy as np
from numpy.random import RandomState

# Parameters
context_size = snakemake.config['context_size']
rand = RandomState(1618820) # Student number as random seed

normal_data = np.loadtxt(snakemake.input[0], skiprows=1, delimiter="\t", dtype=str)
tumor_data = np.loadtxt(snakemake.input[1], skiprows=1, delimiter="\t", dtype=str)

# Indices already used that should not be sampled for Normal data
used_idx = []

# Indices of germline variant and somatic variant elements (labels cropped by numpy)
germline_variants_idx = np.where(normal_data[:,-1] == "GermlineVariant")[0]
somatic_variants_idx = np.where(tumor_data[:,-1] == "SomaticVariant")[0]

# Building germline_variant data points
germline_variants = np.zeros((len(germline_variants_idx),4,2*context_size+1))

for i in range(len(germline_variants_idx)):
	data_id = germline_variants_idx[i]

	entry = np.zeros((4, 2*context_size+1))

	for n in range(-context_size, context_size+1):
		# Normal channels
		entry[0,context_size + n] = normal_data[data_id+n,2]
		entry[1,context_size + n] = normal_data[data_id+n,3]

		# Tumor channels
		entry[2,context_size + n] = tumor_data[data_id+n,2]
		entry[3,context_size + n] = tumor_data[data_id+n,3]

		used_idx.append(data_id+n)

	germline_variants[i] = entry

# Building somatic variant data points
somatic_variants = np.zeros((len(somatic_variants_idx),4,2*context_size+1))

for i in range(len(somatic_variants_idx)):
	data_id = somatic_variants_idx[i]

	entry = np.zeros((4, 2*context_size+1))

	for n in range(-context_size, context_size+1):
		# Normal channels
		entry[0,context_size + n] = normal_data[data_id+n,2]
		entry[1,context_size + n] = normal_data[data_id+n,3]

		# Tumor channels
		entry[2,context_size + n] = tumor_data[data_id+n,2]
		entry[3,context_size + n] = tumor_data[data_id+n,3]

		used_idx.append(data_id+n)

	somatic_variants[i] = entry

# Indices of normal elements
normals_idx = np.intersect1d(np.where(normal_data[:,-1] == "Normal")[0], np.where(tumor_data[:,-1] == "Normal")[0])

# Filtering used indices
used_idx = np.array(used_idx)
to_remove = np.isin(normals_idx, used_idx, invert=True)

normals_idx = normals_idx[to_remove]

# Limit number of normal samples to the sum of the number of germline and somatic variant samples
normal_samples_num = len(germline_variants_idx) + len(somatic_variants_idx)
# Drawing sample indices

normal_samples = rand.choice(normals_idx, normal_samples_num)

normals = np.zeros((normal_samples_num,4,2*context_size+1))

# Building normal datapoints
for i in range(normal_samples_num):
	data_id = normal_samples[i]

	entry = np.zeros((4, 2*context_size+1))

	for n in range(-context_size, context_size+1):
		# Normal channels
		entry[0,context_size + n] = normal_data[data_id+n,2]
		entry[1,context_size + n] = normal_data[data_id+n,3]

		# Tumor channels
		entry[2,context_size + n] = tumor_data[data_id+n,2]
		entry[3,context_size + n] = tumor_data[data_id+n,3]

	normals[i] = entry

# Merge and create labels
dataset = np.concatenate((germline_variants, somatic_variants, normals))
germline_variants_labels = np.array(len(germline_variants_idx)*[[1,0,0]])
somatic_variants_labels = np.array(len(somatic_variants_idx)*[[0,1,0]])
normal_labels = np.array(normal_samples_num*[[0,0,1]])
labels = np.concatenate((germline_variants_labels, somatic_variants_labels, normal_labels))

# Shuffle everything
shuffle_order = rand.permutation(dataset.shape[0])
dataset = dataset[shuffle_order]
labels = labels[shuffle_order]

# Save the result
np.save(snakemake.output[0], dataset)
np.save(snakemake.output[1], labels)