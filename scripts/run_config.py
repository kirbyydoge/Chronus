import itertools
from .calc_rh_parameters import *

SECONDS_IN_MINUTE = 60

# Slurm username
SLURM_USERNAME = "$USER" 

# Maximum Slurm jobs
MAX_SLURM_JOBS = 500 

# Delay between submitting Slurm jobs (while job limit is not reached)
SLURM_SUBMIT_DELAY = 0.1 

# Delay between retrying Slurm job submission (when job limit is reached)
SLURM_RETRY_DELAY = 1 * SECONDS_IN_MINUTE 

# Number of threads used for the personal computer runs
PERSONAL_RUN_THREADS = 4

# Memory histogram precision
MEM_HIST_PREC = 5

# Number of instructions the slowest core must execute before the simulation ends
NUM_EXPECTED_INSTS = 100_000_000

# Number of cycles the simulation should run
NUM_MAX_CYCLES = 100_000_000

CONTROLLER = "BHDRAMController"
SCHEDULER = "BHScheduler"
RFMMANAGER = 2
COLUMN_CAP = 16
TREFI_TRR_RATE = 2

mitigation_list = []
tRH_list = []
flat_thresh_list = []
dynamic_thresh_list = []
thresh_type_list = []
cache_only_list = []

# List of evaluated RowHammer mitigation mechanisms
mitigation_list = ["Chronus", "Chronus+PB", "Graphene", "Hydra", "PARA", "PRAC-4", "PRAC-2", "PRAC-1", "PRAC-RFM", "RFM"]

# List of evaluated RowHammer thresholds
tRH_list = [1024, 512, 256, 128, 64, 32, 20]

params_list = [
    mitigation_list,
    tRH_list,
]

PARAM_STR_LIST = [
    "mitigation",
    "tRH",
]

def get_multicore_params_list():
    params = list(itertools.product(*params_list))
    params.append(("Dummy", 0))
    for mitigation in mitigation_list:
        for tRH in tRH_list:
            params.append((mitigation, tRH))
    return params

def get_singlecore_params_list():
    return [("Dummy", 0)]

def get_trace_lists(trace_combination_file):
    trace_comb_line_count = 0
    multicore_trace_list = set()
    singlecore_trace_list = set()
    with open(trace_combination_file, "r") as f:
        for line in f:
            trace_comb_line_count += 1
            line = line.strip()
            tokens = line.split(',')
            trace_name = tokens[0]
            trace_list = tokens[2:]
            for trace in trace_list:
                singlecore_trace_list.add(trace)
            multicore_trace_list.add(trace_name)
    return singlecore_trace_list, multicore_trace_list

def make_stat_str(param_list, delim="_"):
    return delim.join([str(param) for param in param_list])

def add_mitigation(config, mitigation, tRH):
    if mitigation == "Graphene":
        num_table_entries, activation_threshold, reset_period_ns = get_graphene_parameters(tRH)
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "Graphene",
                "num_table_entries": num_table_entries,
                "activation_threshold": activation_threshold,
                "reset_period_ns": reset_period_ns
        }})
    elif mitigation == "Hydra":
        hydra_tracking_threshold, hydra_group_threshold, hydra_row_group_size, hydra_reset_period_ns, hydra_rcc_num_per_rank, hydra_rcc_policy = get_hydra_parameters(tRH)
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "Hydra",
                "hydra_tracking_threshold": hydra_tracking_threshold,
                "hydra_group_threshold": hydra_group_threshold,
                "hydra_row_group_size": hydra_row_group_size,
                "hydra_reset_period_ns": hydra_reset_period_ns,
                "hydra_rcc_num_per_rank": hydra_rcc_num_per_rank,
                "hydra_rcc_policy": hydra_rcc_policy
        }})
    elif mitigation == "PARA":
        threshold = get_para_parameters(tRH)
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "PARA",
                "threshold": threshold
        }})
    elif mitigation == "RRS":
        num_hrt_entries, num_rit_entries, rss_threshold, reset_period_ns = get_rrs_parameters(tRH)
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "RRS",
                "reset_period_ns": reset_period_ns,
                "rss_threshold": rss_threshold,
                "num_rit_entries": num_rit_entries,
                "num_hrt_entries": num_hrt_entries
        }})
    elif mitigation == "AQUA":
        art_threshold, num_art_entries, num_qrows_per_bank, num_fpt_entries, reset_period_ns = get_aqua_parameters(tRH)
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "AQUA",
                "art_threshold": art_threshold,
                "num_art_entries": num_art_entries,
                "num_qrows_per_bank": num_qrows_per_bank,
                "num_fpt_entries": num_fpt_entries,
                "reset_period_ns": reset_period_ns 
        }})
    elif mitigation == "RFM":
        rfm_thresh = get_rfm_parameters(tRH)
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "ThrottleRFM"
        }})
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "RFMManager",
                "rfm_thresh": rfm_thresh,
                "rfm_plus": False
        }})
    elif mitigation == "RFMplus":
        rfm_thresh = get_rfmplus_parameters(tRH)
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "ThrottleRFM"
        }})
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "RFMManager",
                "rfm_thresh": rfm_thresh,
                "rfm_plus": True
        }})
    elif mitigation == "TWiCe-Ideal":
        twice_rh_threshold, twice_pruning_interval_threshold = get_twice_parameters(tRH)
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "TWiCe-Ideal",
                "twice_rh_threshold": twice_rh_threshold,
                "twice_pruning_interval_threshold": twice_pruning_interval_threshold
        }})
    elif mitigation == "Dummy":
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "DummyMitigation"
        }})
    elif mitigation == "BlockHammer":
        config["MemorySystem"][CONTROLLER][SCHEDULER]["impl"] = "BlockingScheduler"
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "BlockHammerPlugin",
                "bf_num_rh": tRH,
                "bf_ctr_thresh": int(tRH // 4)
        }})
    elif mitigation == "REGA":
        tRAS, V, T = get_rega_parameters(tRH)
        config["MemorySystem"]["DRAM"]["tRAS"] = tRAS
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "ThrottleREGA",
                "V": V,
                "T": T
        }})
    elif mitigation == "PRAC-4":
        abo_threshold = get_prac_parameters(tRH, ABO_refs=4)
        config["MemorySystem"]["DRAM"]["PRAC"] = True
        config["MemorySystem"][CONTROLLER]["impl"] = "PRACDRAMController"
        config["MemorySystem"][CONTROLLER][SCHEDULER]["impl"] = "PRACScheduler"
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "PRAC",
                "abo_threshold": abo_threshold,
                "abo_delay_acts": 4,
                "abo_recovery_refs": 4
        }})
    elif mitigation == "PRAC-2":
        abo_threshold = get_prac_parameters(tRH, ABO_refs=2)
        config["MemorySystem"]["DRAM"]["PRAC"] = True
        config["MemorySystem"][CONTROLLER]["impl"] = "PRACDRAMController"
        config["MemorySystem"][CONTROLLER][SCHEDULER]["impl"] = "PRACScheduler"
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "PRAC",
                "trefi_vrr_rate": TREFI_TRR_RATE,
                "abo_threshold": abo_threshold,
                "abo_delay_acts": 2,
                "abo_recovery_refs": 2
        }})
    elif mitigation == "PRAC-1":
        abo_threshold = get_prac_parameters(tRH, ABO_refs=1)
        config["MemorySystem"]["DRAM"]["PRAC"] = True
        config["MemorySystem"][CONTROLLER]["impl"] = "PRACDRAMController"
        config["MemorySystem"][CONTROLLER][SCHEDULER]["impl"] = "PRACScheduler"
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "PRAC",
                "trevi_vrr_rate": TREFI_TRR_RATE,
                "abo_threshold": abo_threshold,
                "abo_delay_acts": 1,
                "abo_recovery_refs": 1,
        }})
    elif mitigation == "PRAC-RFM":
        abo_threshold, rfm_thresh = get_pracrfm_parameters(tRH)
        config["MemorySystem"]["DRAM"]["PRAC"] = True
        config["MemorySystem"][CONTROLLER]["impl"] = "PRACDRAMController"
        config["MemorySystem"][CONTROLLER][SCHEDULER]["impl"] = "PRACScheduler"
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "PRAC",
                "trevi_vrr_rate": TREFI_TRR_RATE,
                "abo_threshold": abo_threshold,
                "abo_delay_acts": 4,
                "abo_recovery_refs": 4,
        }})
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "RFMManager",
                "rfm_thresh": rfm_thresh,
        }})
    elif mitigation == "Chronus":
        config["MemorySystem"]["DRAM"]["PRAC"] = False
        config["MemorySystem"]["DRAM"]["chronus_enable"] = True
        config["MemorySystem"]["DRAM"]["chronus_energy_factor"] = 1.1907 # SPICE sims
        config["MemorySystem"][CONTROLLER]["impl"] = "ChronusDRAMController"
        config["MemorySystem"][CONTROLLER][SCHEDULER]["impl"] = "PRACScheduler"
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "Chronus",
                "trevi_vrr_rate": TREFI_TRR_RATE,
                "abo_threshold": tRH - 4
        }})
    elif mitigation == "Chronus+PB":
        abo_threshold = get_prac_parameters(tRH, ABO_refs=4)
        config["MemorySystem"]["DRAM"]["PRAC"] = False
        config["MemorySystem"]["DRAM"]["chronus_enable"] = True
        config["MemorySystem"]["DRAM"]["chronus_energy_factor"] = 1.1907 # SPICE sims
        config["MemorySystem"][CONTROLLER]["impl"] = "PRACDRAMController"
        config["MemorySystem"][CONTROLLER][SCHEDULER]["impl"] = "PRACScheduler"
        config["MemorySystem"][CONTROLLER]["plugins"].append({
            "ControllerPlugin" : {
                "impl": "PRAC",
                "trevi_vrr_rate": TREFI_TRR_RATE,
                "abo_threshold": abo_threshold,
                "abo_delay_acts": 4,
                "abo_recovery_refs": 4
        }})