#!/bin/bash -e
#SBATCH --job-name=CkSylArrayJob             # job name (shows up in the queue)
#SBATCH --output s2_logs.txt
#SBATCH --open-mode append                # append output into one file
#SBATCH --time=01:00:00                 # Walltime (HH:MM:SS)
#SBATCH --mem=8GB                     # Memory
#SBATCH --array=0-576                     # Array jobs

module load Maven/3.6.0
module load Python/3.9.5-gimkl-2020a


srun python s2_pmd_ana_app_ARR.py -idx "${SLURM_ARRAY_TASK_ID}" -t 577 -crd ../my_codesnippet_analysis/pmd1 -ucrd -pd mvn_apps -upd -xrf pmdxmlreports_xml -uxrf -ef pmderrorsnippets_java -lf pmd_logs.txt