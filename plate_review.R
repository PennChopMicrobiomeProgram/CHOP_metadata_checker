library(optparse)
library(tidyverse)
library(reshape2)

option_list = list(
  make_option(c("-w", "--workdir"), type="character", default=getwd(),
              help="Set working directory [default= %default]", metavar="character"),
  make_option(c("-r", "--runtype"), type="character", default="Shotgun",
              help="One of [Amplicon, Shotgun, or WGS] for 16S / ITS, Hiseq / Novaseq, or whole genome sequencing, respectively", metavar="character"),
  make_option(c("-m", "--metadata"), type="character", default="CHOPMC-634_meta.txt",
              help="Metadata file gotten from the sequencing lab (usually via slack)", metavar="character")
);

opt_parser = OptionParser(option_list=option_list);
opt = parse_args(opt_parser);

# check runtype is provided
if(!is.null(opt$runtype) & opt$runtype %in% c("Amplicon", "Shotgun", "WGS")) {
  run_type <- opt$runtype
} else {
  stop("Run type must be one of [Amplicon, Shotgun, or WGS]")
}

# getwd
work_dir <- opt$workdir
s_fp <- file.path(work_dir, opt$metadata)

# read the main sample sheet
fp_base <- sub("(.*)\\..*$", "\\1", s_fp)

fp_loc <- paste0(fp_base, "_withLoc.tsv")

fp_plate <- paste0(fp_base, "_plateView.tsv")


s_main <- read.delim(s_fp, stringsAsFactors=F) %>%
  #filter out rows with NA's or blanks
  filter(rowSums(is.na(.)|.=="") != ncol(.)) %>% 
  ##filter out NA or empty columns 
  select_if(function(x) !(all(is.na(x)) | all(x==""))) %>% 
  mutate(SampleID = gsub("^\\s+|\\s+$", "", as.character(SampleID))) %>% ##remove space at the beging and end
  mutate(SampleID = gsub("\\+|-|_|\\(", ".", SampleID)) %>% #change to . if any
  mutate(SampleID = gsub("\\)","",SampleID)) %>% 
  mutate(SampleID = ifelse(grepl("^[0-9]", SampleID), paste0("s.",SampleID),SampleID)) #%>% ##add letter s. if does not start with letter

  
  ##just for this metadata
 
  

if (length(unique(s_main$SampleID)) != dim(s_main)[1]) {
  stop("Duplicated SampleID s")
}


# number of controls per plate; should be 1 of each control per plate; this can be edited to 2 
pos_ctrl_num <- 1
neg_ctrl_num <- 1

blankwell <- 1
blankswab <- 1



num_samples <- dim(s_main)[1]

# colname names
amplicon_cols <- c("SampleID", "investigator", "project_name", "tube_barcode", "box_id", "box_position", "SampleType",
                   "subject_id", "host_species", "study_day", "study_group", "current_antibiotics", "date_collected",
                   "time_collected", "mouse_strain", "cage_id", "plate",  "plate_row", "plate_column",
                   "extract_id", "qiacube_id", "extract_date", "extract_notes", "reverse_barcode_plate",
                   "reverse_barcode_location",  "forward_barcode","dna_conc_ng_ul","redo_dna_conc_ng_ul","final_dna_conc_ng_ul",
                   "polymerase", "library_conc_ng_ul", "column peaks_present","redo_library_conc_ng_ul", "final_library_conc_ng_ul","note_lib_conc",
                   "Ct_ave", "final_ng_per_ul", "total_genomic_copies_per_ul", 
                   "vol_epMotion_ul", "pooled", "miseq_id", "flow_cell_lane","flow_cell_id", "run_start_date",'CHOPMC_Number')

shotgun_cols <- c("SampleID", "investigator", "project_name", "tube_barcode", "box_id", "box_position", "SampleType",
                  "subject_id", "host_species", "study_day", "study_group", "current_antibiotics", "date_collected",
                  "time_collected", "mouse_strain", "cage_id", "plate",  "plate_row", "plate_column",
                  "extract_id", "qiacube_id", "extract_date", "extract_notes", "dna_conc_ng_ul", "redo_dna_conc_ng_ul",
                  "final_dna_conc_ng_ul","Ct_ave", "final_ng_per_ul", "total_genomic_copies_per_ul", "barcode_index_set", 
                  "udi_coord", "Primer_version","library_conc_ng_ul", "redo_library_conc_ng_ul", "final_library_conc_ng_ul","note_lib_conc",
                  "vol_epMotion_ul", "pooled", "flow_cell_lane", "flow_cell_id", "NovaSeq600_id", 
                  "run_start_date",'CHOPMC_Number')

if (!all(c("SampleID", "SampleType") %in% colnames(s_main))) {
  stop("Please make sure the sample sheet has both SampleID and SampleType column names.")
}
if (any(c("plate","plate_row","plate_column","plate_location_combined") %in% colnames(s_main))) {
  stop("Please make sure the sample sheet does not have these column names: plate, plate_row, plate_column, plate_location_combined")
}

#leaving in the extra wells in case a project needs 2 of certain controls per plate
extractswab_df <- data.frame(plate_location_combined = c("G01", "D05"), SampleID = rep("Extractblankswab", 2),
                             for_unique = c(1,2), SampleType = rep("Blank swab", 2), stringsAsFactors=FALSE)
extractwell_df <- data.frame(plate_location_combined = c("E07", "H10"), SampleID = rep("Extractemptywell", 2),
                             for_unique = c(1,2), SampleType = rep("Empty well", 2), stringsAsFactors=FALSE)
freewater_df <- data.frame(plate_location_combined = c("C09", "E12"), SampleID = rep("DNAfreewater", 2),
                           for_unique = c(1,2), SampleType = rep("DNA-free water", 2), stringsAsFactors=FALSE)
mockdna_df <- data.frame(plate_location_combined = c("G03", "A04"), SampleID = rep("mockdna", 2),
                         for_unique = c(1,2), SampleType = rep("Mock DNA", 2), stringsAsFactors=FALSE)

num_plates <- ceiling(num_samples/(96-sum(pos_ctrl_num+neg_ctrl_num+blankwell+blankswab)))

controls <- rbind(extractswab_df[0:blankswab, ], extractwell_df[0:blankwell, ], freewater_df[0:neg_ctrl_num, ], mockdna_df[0:pos_ctrl_num, ])

s <- expand.grid(plate_row = LETTERS[1:8], plate_column = sprintf("%02d", 1:12)) %>%
  mutate(plate_location_combined = paste0(plate_row, plate_column))

s <- do.call("rbind", replicate(num_plates, s, simplify=F)) %>%
  mutate(plate = rep(1:num_plates, each=96)) %>%
  left_join(controls, by="plate_location_combined") %>%
  mutate(for_unique = for_unique + (plate-1)*2) %>%
  mutate(for_timestamp = strftime(Sys.time(), "%Y%m%d")) %>%
  mutate(SampleID = ifelse(
    is.na(SampleID), NA, paste0(SampleID, for_unique, ".", for_timestamp))) %>%
  select(-for_unique, -for_timestamp)

# for the last plate, if the number of samples on there is between 32 and 48, switch DNA-free water to position D05 only on this plate
samps_on_plate <- num_samples+((num_plates-1)*4)
if(samps_on_plate%%96 >= 32 & samps_on_plate%%96 < 48) {
  s[s$plate==num_plates,]
  s[s$plate==num_plates & s$plate_row=="D" & s$plate_column=="05", c("SampleID", "SampleType")] <-
    s[s$plate==num_plates & s$plate_row=="E" & s$plate_column=="07", c("SampleID", "SampleType")]
  s[s$plate==num_plates & s$plate_row=="E" & s$plate_column=="07", c("SampleID", "SampleType")] <- NA
}

#################################
# remove/add controls here if need to
#################################
# s <- s %>%
#   mutate(SampleID = ifelse(plate%%2==0, NA, SampleID)) %>%
#   mutate(SampleType = ifelse(plate%%2==0, NA, SampleType))

#################################

s$SampleID[which(is.na(s$SampleID))[1:length(s_main$SampleID)]] <- s_main$SampleID

# find the blank wells in the last plate
blanks <- which(is.na(s$SampleID))

non_blanks <- which(!is.na(s$SampleID))

non_blanks_toShift <- non_blanks[non_blanks > blanks[1]]

# find non-full plates and column; there shouldn't be more than one plate with missing entries
non_full_plate <- s[blanks[1], "plate"]
non_full_col <- as.numeric(levels(s[blanks[1], "plate_column"])[s[blanks[1], "plate_column"]])
non_full_row <- levels(s[blanks[1], "plate_row"])[s[blanks[1], "plate_row"]]

# if there is only a couple of non-filled wells between the last sample and the next control well, put the latter controls in-between this control's position
non_blank_interval <- non_blanks[diff(non_blanks) > 1]
if((length(non_blank_interval) > 1) & (non_blank_interval[2] - non_blank_interval[1] <= length(non_blanks_toShift))) {
  # remove the first non_blank_toShift to keep its position
  non_blanks_toShift <- non_blanks_toShift[2:length(non_blanks_toShift)]
}

# shift controls up if missing in middle
if (length(non_blanks_toShift) > 0 & length(blanks > 0)) {
  
  non_blankIDs <- s[non_blanks_toShift, c("SampleID", "SampleType")]
  s[non_blanks_toShift, c("SampleID", "SampleType")] <- NA
  blanks <- which(is.na(s$SampleID))
  s[blanks[1:dim(non_blankIDs)[1]], c("SampleID", "SampleType")] <- non_blankIDs
  
}

# merge with Sample info
s <- left_join(s, s_main, by="SampleID") %>%
  mutate(SampleType.x = ifelse(is.na(SampleType.x), SampleType.y, SampleType.x)) %>%
  rename(SampleType = SampleType.x) %>%
  select(-SampleType.y) %>%
  select(-one_of(c("plate_row", "plate_column", "plate_location_combined", "plate")), everything())

# error checks
if (!all(s_main$SampleID %in% s$SampleID)) {
  lost_ids <- paste(s_main$SampleID[!s_main$SampleID %in% s$SampleID], collapse=', ')
  stop(paste('Oh no! Some of the samples got lost!', lost_ids))
}

if (file.exists(fp_plate)) {
  file.remove(fp_plate)
  message(paste("Plate view file already exists. Overwriting the file:", fp_plate))
}

#add columns that lab wants
if (run_type %in% "Amplicon") {
  cols_to_add <- amplicon_cols[!amplicon_cols %in% colnames(s)]
} else if (run_type %in% c("Shotgun", "WGS")) {
  cols_to_add <- shotgun_cols[!shotgun_cols %in% colnames(s)]
} else { simpleWarning("Do you have a typo in your run_type? Otherwise no columns are being added!") }

s[,cols_to_add] <- ""


# write the updated map to file

write.table(filter(s, !is.na(SampleID)), fp_loc, sep ='\t', quote=FALSE, row.names = FALSE)

# write the plate view to file
for (i in 1:num_plates) {
  to_write <- s %>%
    filter(plate == i) %>%
    dcast(plate_row ~ plate_column, value.var="SampleID")
  colnames(to_write)[1] <- paste0("plate", i)
  suppressWarnings(write.table(to_write, file=fp_plate, append=TRUE, quote=F, sep='\t', row.names=F, na=""))
  write("\n",file=fp_plate,append=TRUE)
}


