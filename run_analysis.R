# Run the NavCity figures and statistics for one analysis folder in 05_analyses.
#
#   cd <nav_study>/04_code/navcity_analysis
#   Rscript run_analysis.R ../../05_analyses/navcity_60subs              # everything
#   Rscript run_analysis.R ../../05_analyses/navcity_60subs figures      # only 2_figures
#   Rscript run_analysis.R ../../05_analyses/navcity_60subs main_lmm     # only one 3_stats folder
#
# The analysis folder must contain sample.tsv (participant_id, age_group). Everything the Rmds
# make goes into <analysis>/output/: figures (.svg/.png) and their reports in output/figures/,
# each statistics folder's tables and reports in output/stats/<folder>/.
#
# Each Rmd runs in its own fresh R session (callr), so packages loaded by one Rmd (e.g. MASS,
# which has its own select()) cannot change how the next one runs. A failing Rmd does not stop
# the others. output/run_log.tsv lists every Rmd, OK/FAILED and the error.

args <- commandArgs(trailingOnly = FALSE)
code_root <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)])))
targs <- commandArgs(trailingOnly = TRUE)
if (length(targs) < 1) stop("Usage: Rscript run_analysis.R <analysis folder> [figures|<stats folder>|<folder>/<file>.Rmd ...]")
analysis_root <- normalizePath(targs[1], mustWork = TRUE)
if (!file.exists(file.path(analysis_root, "sample.tsv"))) stop(analysis_root, " has no sample.tsv")
only <- targs[-1]

# Order matters only within a folder: an LMM before its p-value extraction.
plan <- list(
  figures      = c("1_average_plots.Rmd", "2_by_block_plots.Rmd", "3_by_target_plots.Rmd",
                   "4_corr_plots.Rmd", "5_nara_plots.Rmd", "6_cohorts_average_plots.Rmd",
                   "7_cohorts_by_block_plots.Rmd", "8_cohorts_corr_plots.Rmd"),
  main_lmm     = c("main_lmm_try.Rmd", "extract_pvalues_main.Rmd"),
  cohorts_lmm  = c("cohorts_lmm.Rmd", "extract_pvalues_cohorts.Rmd"),
  corrs        = c("two_grp_corr_stats.Rmd"),
  sensitivity  = c("sensitivity_analysis_teleport_dist_FINAL.Rmd"),
  nara         = c("1_nara_stats.Rmd", "2_determine_nara_cohorts.Rmd", "3_nara_age_stats.Rmd",
                   "4_ya_low_nara_nav_analysis.Rmd", "5_low_nara_nonnav_analysis.Rmd"),
  demographics = c("1_gender_age_stats.Rmd", "2_demographic_stats.Rmd",
                   "2_demographic_stats_redo_SSQ.Rmd", "3_sig_demographic_corrs.Rmd",
                   "3_sig_demographic_corrs_with_correction.Rmd",
                   "4_three_grp_demographic_stats.Rmd", "5_oahigh_oalow_demographic_stats.Rmd",
                   "5_oahigh_oalow_demographic_stats_redo_SSQ.Rmd")
)
# Arguments: whole folders ("figures", "main_lmm") or single Rmds ("figures/1_average_plots.Rmd")
if (length(only)) {
  bad <- setdiff(sub("/.*", "", only), names(plan))
  if (length(bad)) stop("Unknown folder: ", paste(bad, collapse = ", "))
  plan <- lapply(setNames(nm = unique(sub("/.*", "", only))), function(part) {
    picks <- sub("^[^/]*/?", "", only[sub("/.*", "", only) == part])
    if (any(picks == "")) return(plan[[part]])
    miss <- setdiff(picks, plan[[part]])
    if (length(miss)) stop("Not in ", part, ": ", paste(miss, collapse = ", "))
    plan[[part]][plan[[part]] %in% picks]            # keep the folder's order
  })
}

log <- data.frame()
for (part in names(plan)) {
  src <- if (part == "figures") file.path(code_root, "2_figures") else file.path(code_root, "3_stats", part)
  out <- if (part == "figures") file.path(analysis_root, "output", "figures")
         else file.path(analysis_root, "output", "stats", part)
  dir.create(out, recursive = TRUE, showWarnings = FALSE)
  for (rmd in plan[[part]]) {
    cat(sprintf("== %s/%s ... ", part, rmd))
    t0 <- Sys.time()
    base <- sub("\\.Rmd$", "", rmd)
    reports <- function() list.files(out, paste0("^", base, "\\.(html|pdf|docx)$"))
    unlink(file.path(out, reports()))                      # an old report must not count as success
    res <- tryCatch({
      callr::r(function(input, out, code, analysis) {
        Sys.setenv(NAVCITY_CODE = code, ANALYSIS_ROOT = analysis)
        rmarkdown::render(input, output_dir = out, knit_root_dir = out,
                          intermediates_dir = tempdir(), quiet = TRUE)
      }, args = list(file.path(src, rmd), out, code_root, analysis_root), show = FALSE)
      NULL
    }, error = function(e) e)
    # FAILED if R reported an error (even one with an empty message) or no report was written
    ok <- is.null(res) && length(reports()) > 0
    err <- if (is.null(res)) (if (ok) "" else "no report written")
           else { m <- conditionMessage(if (!is.null(res$parent)) res$parent else res)
                  m <- gsub("[\t\n]+", " ", m); if (!nzchar(trimws(gsub("!", "", m)))) "error without a message" else m }
    status <- if (ok) "OK" else "FAILED"
    cat(status, if (!ok) paste0("\n   ", substr(err, 1, 300)), "\n")
    log <- rbind(log, data.frame(part = part, rmd = rmd, status = status,
                                 seconds = round(as.numeric(Sys.time() - t0, units = "secs")),
                                 error = err))
  }
}
dir.create(file.path(analysis_root, "output"), showWarnings = FALSE)
write.table(log, file.path(analysis_root, "output", "run_log.tsv"), sep = "\t", row.names = FALSE, quote = FALSE)
cat("\n", sum(log$status == "OK"), "of", nrow(log), "Rmds ran; see", file.path(analysis_root, "output", "run_log.tsv"), "\n")
