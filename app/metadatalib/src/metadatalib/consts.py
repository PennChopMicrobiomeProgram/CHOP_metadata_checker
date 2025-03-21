ALLOWED_EXTENSIONS = {"tsv", "csv", "txt"}

DEFAULT_SAMPLE_FIELDS = [
    "SampleID",
    "sample_type",
    "subject_id",
    "host_species",
]

CHOP_MANDATORY_TUBE = [
    "SampleID",
    "investigator",
    "sample_type",
]

CHOP_SUGGESTED = [
    "subject_id",
    "host_species",
    "study_day",
    "current_antibiotics",
    "recent_antibiotics",
    "cage_id",
    "mouse_strain",
]

SAMPLE_TYPE_LIST = [
    "Amniotic fluid",
    "BAL",
    "Bedding",
    "Biofilm",
    "Bioreactor",
    "Blank swab",
    "Blood",
    "Breast milk",
    "Buffer",
    "Cecum",
    "Cell lysate",
    "Cervical swab",
    "Cheek swab",
    "Crop",
    "Dental plaque",
    "DNA-free water",
    "Duodenum",
    "Dust",
    "Elution buffer",
    "Empty well",
    "Endometrial swab",
    "Environmental control",
    "Esophageal biopsy",
    "Esophagus",
    "Feces",
    "Feed",
    "Fistula",
    "Fistula swab",
    "Fly food",
    "Fruit fly",
    "Ileostomy fluid",
    "Ileum",
    "Kveim reagent",
    "Lab water",
    "Macular Retina",
    "Meconium",
    "Medium",
    "Microbial culture",
    "Mock DNA",
    "Mouse chow",
    "Nasal swab",
    "Nasopharyngeal swab",
    "Oral swab",
    "Oral wash",
    "Oropharyngeal swab",
    "Ostomy fluid",
    "Pancreatic fluid",
    "PCR water",
    "Peripheral retina",
    "Placenta",
    "Plasma",
    "Rectal biopsy",
    "Rectal swab",
    "Saline",
    "Saliva",
    "Sediment",
    "Serum",
    "Skin swab",
    "Small intestine",
    "Soil",
    "Sputum",
    "Surface swab",
    "Tongue swab",
    "Tonsil",
    "Tracheal aspirate",
    "Tracheal control",
    "Urethral swab",
    "Urine",
    "Water",
    "Weighing paper",
    "Whole gut",
    "Large intestine mucosa",
    "Large intestine lumen",
]

HOST_SPECIES_LIST = [
    "Dog",
    "Fruit fly",
    "Human",
    "Mouse",
    "Naked mole rat",
    "Pig",
    "Pigeon",
    "Rabbit",
    "Rat",
    "Rhesus macaque",
    None,
]

##table to translate what these regex patterns mean
REGEX_TRANSLATE = {
    "^[0-9A-Za-z._]+$": " only contain numbers, letters, underscores, and periods",
    "^[0-9A-Za-z_]+$": " only contain numbers, letters, and underscores",
    "^[A-Za-z]": " only start with capital or lowercase letters",
    "^[0-9A-Za-z._+-\/<>=|,() ]+$": " only contain numbers, letters, spaces, and allowed characters inside the bracket [._+-\/<>=|,()]",
    "^[0-9A-Za-z._-]+$": " only contain numbers, letters, periods, dashes, and underscores",
    "^[0-9]{2}/[0-9]{2}/[0-9]{2}$": " be in format mm/dd/yy",
    "^[0-9]{2}:[0-9]{2}:[0-9]{2}$": " be in format hh:mm:ss",
    "^[A-H][0-9]{2}$": " only contain a letter from A-H and a number 1-12",
    "^[ATCGURYKMSWBDHVN]+$": " only contain nucleotide symbols",
}
