"""Generate realistic test data for PDF_GUI development.

Creates ~25 run directories under tests/test_data/runs/ with varied statuses,
metrics, and version names (including 80-100 char stress cases).
"""

import json
import os
import random
import shutil
from datetime import datetime, timedelta

random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "runs")

STEP_NAMES = ["init", "floorplan", "place", "cts", "route", "routeopt", "STA"]
METRIC_KEYS = ["WNS", "TNS", "max_cap", "max_tran", "leakage"]


def make_job(status: str, runtime: str) -> dict:
    return {
        "job_id": f"lsf_{random.randint(10000, 99999)}",
        "status": status,
        "memory_current_mb": round(random.uniform(2000, 8000), 1),
        "memory_max_mb": round(random.uniform(4000, 16000), 1),
        "memory_avg_mb": round(random.uniform(3000, 10000), 1),
        "cpu_current_pct": round(random.uniform(10, 100), 1),
        "cpu_max_pct": round(random.uniform(50, 100), 1),
        "cpu_avg_pct": round(random.uniform(30, 95), 1),
        "runtime": runtime,
    }


def make_metrics(wns=None, tns=None, cap=None, tran=None, leak=None) -> dict:
    return {
        "WNS": wns,
        "TNS": tns,
        "max_cap": cap,
        "max_tran": tran,
        "leakage": leak,
    }


def write_step_json(dir_path: str, step_name: str, status: str, metrics: dict,
                    job_status: str, runtime: str):
    data = {
        "step": step_name,
        "status": status,
        "metrics": metrics,
        "job": make_job(job_status, runtime),
    }
    with open(os.path.join(dir_path, f"{step_name}.json"), "w") as f:
        json.dump(data, f, indent=2)


def write_run_info(dir_path: str, version_name: str):
    with open(os.path.join(dir_path, "run_info.json"), "w") as f:
        json.dump({
            "version": version_name,
            "flow_name": "Chip Design Flow",
            "created_at": datetime.now().isoformat(),
        }, f, indent=2)


def create_version(base_time: datetime, offset_minutes: int,
                   version_name: str, scenario: str) -> None:
    ts = (base_time + timedelta(minutes=offset_minutes)).strftime("%Y-%m-%d_%H%M")
    dir_name = f"{ts}_{version_name}"
    dir_path = os.path.join(OUTPUT_DIR, dir_name)
    os.makedirs(dir_path, exist_ok=True)
    write_run_info(dir_path, version_name)

    if scenario == "SUCCESS":
        for i, step in enumerate(STEP_NAMES):
            metrics = None
            runtime = f"{random.randint(5, 15)}m"
            if step == "init":
                metrics = make_metrics()
            elif step == "STA":
                metrics = make_metrics(
                    wns=round(random.uniform(-0.050, -0.001), 3),
                    tns=round(random.uniform(-2.0, 0.0), 2),
                    cap=round(random.uniform(0.01, 0.05), 4),
                    tran=round(random.uniform(0.005, 0.03), 4),
                    leak=round(random.uniform(50, 200), 2),
                )
                runtime = f"{random.randint(10, 25)}m"
            elif step in ("place", "cts", "route", "routeopt"):
                metrics = make_metrics(
                    wns=round(random.uniform(-0.200, -0.010), 3),
                    tns=round(random.uniform(-8.0, -0.5), 2),
                    cap=round(random.uniform(0.01, 0.08), 4),
                    tran=round(random.uniform(0.005, 0.04), 4),
                    leak=round(random.uniform(80, 250), 2),
                )
                runtime = f"{random.randint(15, 45)}m"
            else:
                metrics = make_metrics(
                    cap=round(random.uniform(0.01, 0.10), 4),
                    tran=round(random.uniform(0.005, 0.05), 4),
                )
            write_step_json(dir_path, step, "SUCCESS", metrics, "SUCCESS", runtime)

    elif scenario == "RUNNING":
        running_idx = len(STEP_NAMES) - 1
        for i, step in enumerate(STEP_NAMES):
            if i < running_idx:
                status = "SUCCESS"
                job_status = "SUCCESS"
                runtime = f"{random.randint(5, 40)}m"
                metrics = make_metrics(
                    wns=round(random.uniform(-0.150, -0.010), 3),
                    tns=round(random.uniform(-5.0, -0.5), 2),
                    cap=round(random.uniform(0.01, 0.06), 4),
                    tran=round(random.uniform(0.005, 0.03), 4),
                    leak=round(random.uniform(80, 200), 2),
                )
            elif i == running_idx:
                status = "RUNNING"
                job_status = "RUNNING"
                runtime = f"{random.randint(5, 20)}m so far"
                metrics = make_metrics(
                    wns=round(random.uniform(-0.100, -0.005), 3),
                    tns=round(random.uniform(-3.0, 0.0), 2),
                )
            else:
                status = "PENDING"
                job_status = "PENDING"
                runtime = ""
                metrics = make_metrics()
            if status == "PENDING":
                continue
            write_step_json(dir_path, step, status, metrics, job_status, runtime)

    elif scenario == "FAIL":
        fail_idx = random.randint(3, 5)  # fail at cts, route, or routeopt
        for i, step in enumerate(STEP_NAMES):
            if i < fail_idx:
                status = "SUCCESS"
                job_status = "SUCCESS"
                runtime = f"{random.randint(5, 40)}m"
                metrics = make_metrics(
                    wns=round(random.uniform(-0.200, -0.050), 3),
                    tns=round(random.uniform(-6.0, -1.0), 2),
                    cap=round(random.uniform(0.01, 0.07), 4),
                    tran=round(random.uniform(0.005, 0.04), 4),
                    leak=round(random.uniform(80, 250), 2),
                )
            elif i == fail_idx:
                status = "FAIL"
                job_status = "FAIL"
                runtime = f"{random.randint(20, 60)}m"
                metrics = make_metrics(
                    wns=round(random.uniform(-0.500, -0.200), 3),
                    tns=round(random.uniform(-25.0, -8.0), 2),
                    cap=round(random.uniform(0.10, 0.30), 4),
                    tran=round(random.uniform(0.05, 0.15), 4),
                    leak=round(random.uniform(200, 400), 2),
                )
            else:
                status = "PENDING"
                job_status = "PENDING"
                runtime = ""
                metrics = make_metrics()
            if status == "PENDING":
                continue
            write_step_json(dir_path, step, status, metrics, job_status, runtime)

    elif scenario == "PENDING":
        cutoff = random.randint(1, 2)
        for i, step in enumerate(STEP_NAMES):
            if i < cutoff:
                status = "SUCCESS"
                job_status = "SUCCESS"
                runtime = f"{random.randint(5, 20)}m"
                metrics = make_metrics(
                    cap=round(random.uniform(0.01, 0.05), 4),
                    tran=round(random.uniform(0.005, 0.03), 4),
                )
            else:
                status = "PENDING"
                job_status = "PENDING"
                runtime = ""
                metrics = make_metrics()
            if status == "PENDING":
                continue
            write_step_json(dir_path, step, status, metrics, job_status, runtime)


def main():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    base_time = datetime.now()

    # 5 SUCCESS versions
    success_names = [
        "chip_A_golden",
        "chip_B_production",
        "chip_C_signed_off",
        "chip_D_release",
        "chip_E_final",
    ]
    for i, name in enumerate(success_names):
        create_version(base_time, i * 30, name, "SUCCESS")

    # 5 RUNNING versions
    running_names = [
        "chip_A_eco_v2",
        "chip_B_hotfix",
        "chip_F_test_opt",
        "chip_G_power_tuning",
        "chip_H_area_reduction",
    ]
    for i, name in enumerate(running_names):
        create_version(base_time, 150 + i * 30, name, "RUNNING")

    # 5 FAIL versions
    fail_names = [
        "chip_I_experiment",
        "chip_J_aggressive",
        "chip_K_retry_v1",
        "chip_L_broken_floorplan",
        "chip_M_timing_fail",
    ]
    for i, name in enumerate(fail_names):
        create_version(base_time, 300 + i * 30, name, "FAIL")

    # 5 PENDING-heavy versions
    pending_names = [
        "chip_N_just_started",
        "chip_O_early_phase",
        "chip_P_waiting_queue",
        "chip_Q_new_branch",
        "chip_R_fresh_run",
    ]
    for i, name in enumerate(pending_names):
        create_version(base_time, 450 + i * 30, name, "PENDING")

    # 5 long-name stress versions
    long_names = [
        "chip_X_ultra_aggressive_floorplan_experiment_v3_with_custom_clock_mesh_and_retention_islands",
        "chip_Y_multi_corner_multi_mode_optimization_run_with_advanced_power_gating_strategy_final",
        "chip_Z_experimental_3d_ic_integration_with_hybrid_bonding_and_through_silicon_via_analysis",
        "chip_W_low_power_iot_sensor_node_with_aggressive_voltage_scaling_and_adaptive_body_bias",
        "chip_V_high_performance_compute_tile_with_hbm3_memory_stack_and_custom_network_on_chip",
    ]
    for i, name in enumerate(long_names):
        create_version(base_time, 600 + i * 30, name, random.choice(
            ["SUCCESS", "RUNNING", "FAIL"]))

    print(f"Generated test data in: {OUTPUT_DIR}")
    print(f"Total versions: {len(os.listdir(OUTPUT_DIR))}")


if __name__ == "__main__":
    main()
