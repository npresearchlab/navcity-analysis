# Shared setup, loaded at the top of every Rmd in 2_figures/ and 3_stats/:
#   source(file.path(Sys.getenv("NAVCITY_CODE"), "setup.R"), local = TRUE)
# run_analysis.R sets the two environment variables:
#   NAVCITY_CODE   this folder (04_code/navcity_analysis)
#   ANALYSIS_ROOT  the analysis folder in 05_analyses: its sample.tsv says who is analysed,
#                  and all outputs go to its output/ folder
#
# Data is read where it lives; nothing is copied:
#   navcity_path     NavCity outcome tables (corrected), 03_data/derivatives/navcity/
#   paper_data_path  NARA, cognitive scores, demographics as the NavAging paper used them,
#                    06_releases/paper_navaging/data/ (read only)
# The NavCity tables hold everyone included in the study; reading them through read.csv /
# read_csv here keeps only the participants in the analysis's sample.tsv.

analysis_root <- Sys.getenv("ANALYSIS_ROOT")
code_root     <- Sys.getenv("NAVCITY_CODE")
if (analysis_root == "" || code_root == "")
  stop("Run with run_analysis.R, or first Sys.setenv(NAVCITY_CODE = '<nav_study>/04_code/navcity_analysis', ",
       "ANALYSIS_ROOT = '<nav_study>/05_analyses/<analysis>')")
study_root      <- normalizePath(file.path(code_root, "..", ".."))
navcity_path    <- file.path(study_root, "03_data", "derivatives", "navcity")
paper_data_path <- file.path(study_root, "06_releases", "paper_navaging", "data")

sample_ids <- utils::read.delim(file.path(analysis_root, "sample.tsv"),
                                stringsAsFactors = FALSE)$participant_id

.navcity_tables <- c("ya_merged_results.csv", "oa_merged_results.csv",
                     "ya_averaged_results.csv", "oa_averaged_results.csv")

# Keep only the sample's participants when the file is a NavCity table
.keep_sample <- function(d, file) {
  if (is.character(file) && basename(file) %in% .navcity_tables) {
    group <- toupper(substr(basename(file), 1, 2))                  # YA / OA
    want <- sample_ids[grepl(paste0("^", group, "$"),
                             utils::read.delim(file.path(analysis_root, "sample.tsv"))$age_group)]
    missing <- setdiff(want, d$Participant)
    if (length(missing)) stop(basename(file), ": no NavCity data for ", paste(missing, collapse = ", "))
    d <- d[d$Participant %in% sample_ids, , drop = FALSE]
  }
  d
}

# The Rmds call read.csv() / read_csv(); these versions add the sample filter above.
read.csv <- function(file, ...) .keep_sample(utils::read.csv(file, ...), file)
read_csv <- function(file, ...) .keep_sample(readr::read_csv(file, ...), file)

# ---------------------------------------------------------------------------------------------
# Fixes for the paper's code (added 2026-11-11; each use is marked "FIX" in the Rmd)

# Some of the paper's Rmds were written for a version of the NARA / demographics files that had
# Group as "YA" / "OA" and an Age (years) column. The paper's frozen files have Group as 0 / 1
# (0 = YA, 1 = OA; checked against sample.tsv for all 60) and Age only in demographic_data.csv.
# This adds both, so those Rmds run unchanged otherwise. Age comes from the paper's
# demographic_data.csv (same values the paper used).
label_paper_groups <- function(d) {
  names(d) <- sub("^Age\\.?$", "Age", trimws(names(d)))           # "Age " in demographic_data.csv
  if (is.numeric(d$Group) && all(d$Group %in% c(0, 1, NA)))
    d$Group <- c("YA", "OA")[d$Group + 1]
  if (!"Age" %in% names(d)) {
    demo <- utils::read.csv(file.path(paper_data_path, "demographic_data.csv"), check.names = FALSE)
    names(demo) <- trimws(names(demo))
    d$Age <- demo$Age[match(d$Participant, demo$Participant)]
  }
  d
}

# Replacement for gghalves::geom_half_point(side = "l"), which does not work with ggplot2 4
# (gghalves is no longer maintained). Points are jittered as before and then shifted to the
# left of the box: geom_point(position = position_jitter_left(...)).
position_jitter_left <- function(width = 0.12, shift = 0.2, seed = 1) {
  ggplot2::ggproto(NULL, ggplot2::PositionJitter,
    compute_layer = function(self, data, params, layout) {
      data <- ggplot2::ggproto_parent(ggplot2::PositionJitter, self)$compute_layer(data, params, layout)
      data$x <- data$x - shift
      data
    },
    setup_params = function(self, data) list(width = width, height = 0, seed = seed)
  )
}
