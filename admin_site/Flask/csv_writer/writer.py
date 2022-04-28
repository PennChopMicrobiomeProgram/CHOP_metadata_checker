from db.db import MetadataDB

# Helper function for generating a csv string for flask to download
# @param submission_id is the id of the submissions to download
# @return is the csv in string form for flask to output
def generate_csv(db: MetadataDB, submission_id: int) -> str:
    samples = db.list_samples(submission_id)
    annotations = []
    for sample in samples:
        annotations.append(db.list_annotations(sample[0]))
    annotations = [item for sublist in annotations for item in sublist]

    fields = ["SampleID", "sample_type", "subject_id", "host_species"]
    for annotation in annotations:
        if annotation[1] not in fields:
            fields.append(annotation[1])

    sep = '\",\"'
    ret = f"\"{sep.join(fields)}\"\n"
    for sample in samples:
        l = f"\"{sample[1]}\",\"{sample[3]}\",\"{sample[4]}\",\"{sample[5]}\""

        a = {}
        for annotation in annotations:
            if annotation[0] == sample[0]:
                a[annotation[1]] = annotation[2]
        for f in fields[4:]:
            if f in a:
                l += f",\"{a[f]}\""
            else:
                l += ",\"\""
        
        l += "\n"
        ret += l

    return ret
