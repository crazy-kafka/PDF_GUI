"""Generate realistic test data for PDF_GUI development.

Creates ~25 run directories under tests/test_data/runs/ with varied statuses,
metrics, and version names (including 80-100 char stress cases).
"""

import json
import os
import random
import shutil
import sys
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
        # Only the last step is PENDING, all prior are SUCCESS → OverallStatus.PENDING
        for i, step in enumerate(STEP_NAMES):
            if i < len(STEP_NAMES) - 1:
                status = "SUCCESS"
                job_status = "SUCCESS"
                runtime = f"{random.randint(5, 40)}m"
                metrics = make_metrics(
                    wns=round(random.uniform(-0.200, -0.010), 3),
                    tns=round(random.uniform(-8.0, -0.5), 2),
                    cap=round(random.uniform(0.01, 0.08), 4),
                    tran=round(random.uniform(0.005, 0.04), 4),
                    leak=round(random.uniform(80, 250), 2),
                )
            else:
                status = "PENDING"
                job_status = "PENDING"
                runtime = ""
                metrics = make_metrics()
            write_step_json(dir_path, step, status, metrics, job_status, runtime)

    elif scenario == "BRANCH":
        start_idx = random.randint(2, 4)
        for i, step in enumerate(STEP_NAMES):
            if i < start_idx:
                continue
            if step == "STA":
                status = random.choice(["SUCCESS", "RUNNING"])
                job_status = status
                runtime = f"{random.randint(10, 30)}m" if status == "SUCCESS" else f"{random.randint(5, 15)}m so far"
                metrics = make_metrics(
                    wns=round(random.uniform(-0.050, -0.001), 3),
                    tns=round(random.uniform(-2.0, 0.0), 2),
                    cap=round(random.uniform(0.01, 0.05), 4),
                    tran=round(random.uniform(0.005, 0.03), 4),
                    leak=round(random.uniform(50, 200), 2),
                ) if status == "SUCCESS" else make_metrics(
                    wns=round(random.uniform(-0.100, -0.005), 3),
                    tns=round(random.uniform(-3.0, 0.0), 2),
                )
            else:
                status = "SUCCESS"
                job_status = "SUCCESS"
                runtime = f"{random.randint(10, 40)}m"
                metrics = make_metrics(
                    wns=round(random.uniform(-0.200, -0.010), 3),
                    tns=round(random.uniform(-8.0, -0.5), 2),
                    cap=round(random.uniform(0.01, 0.08), 4),
                    tran=round(random.uniform(0.005, 0.04), 4),
                    leak=round(random.uniform(80, 250), 2),
                )
            write_step_json(dir_path, step, status, metrics, job_status, runtime)


def create_sample_reports(version_dirs: list[str]):
    """Create real report/log/picture files so right-click → open works."""
    sample_rpt = """# Sample Timing Report
Scenario: worst-case setup
Corner:   ss_0p6v_125c
WNS:      -0.050 ns
TNS:      -3.450 ns
"""
    sample_log = """[INFO] Starting {step} for {version}
[INFO] Loading design database ...
[INFO] Reading constraints ...
[INFO] Running optimization ...
[INFO] {step} completed successfully
"""
    for dir_path in version_dirs:
        run_info_path = os.path.join(dir_path, "run_info.json")
        version_name = os.path.basename(dir_path)
        if os.path.isfile(run_info_path):
            with open(run_info_path, "r") as f:
                version_name = json.load(f).get("version", version_name)
        for step_name in STEP_NAMES:
            step_json = os.path.join(dir_path, f"{step_name}.json")
            if not os.path.isfile(step_json):
                continue

            # Reports
            report_dir = os.path.join(dir_path, "reports", version_name, step_name)
            os.makedirs(report_dir, exist_ok=True)
            with open(os.path.join(report_dir, "timing.rpt"), "w") as f:
                f.write(f"# Timing Report — {version_name} / {step_name}\n{sample_rpt}")
            with open(os.path.join(report_dir, "wns_summary.rpt"), "w") as f:
                f.write(f"# WNS Summary — {version_name} / {step_name}\nWNS: -0.050\n")

            # Density report + picture
            rpt_dir = os.path.join(dir_path, "rpt", version_name, step_name)
            os.makedirs(rpt_dir, exist_ok=True)
            with open(os.path.join(rpt_dir, "density.rpt"), "w") as f:
                f.write(f"# Density Report — {version_name} / {step_name}\nDensity: 85.2%\n")

            img_dir = os.path.join(dir_path, "img", version_name, step_name)
            os.makedirs(img_dir, exist_ok=True)
            with open(os.path.join(img_dir, "density.png"), "w") as f:
                f.write("# placeholder density image\n")

            # Logs
            log_dir = os.path.join(dir_path, "logs", version_name, step_name)
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "run.log"), "w") as f:
                f.write(sample_log.format(version=version_name, step=step_name))


def _gen_base_30():
    """Generate the base 30 versions (shared by both suites)."""
    base_time = datetime.now()

    # 5 SUCCESS versions
    for i, name in enumerate([
        "chip_A_golden", "chip_B_production", "chip_C_signed_off",
        "chip_D_release", "chip_E_final",
    ]):
        create_version(base_time, i * 30, name, "SUCCESS")

    # 5 RUNNING versions
    for i, name in enumerate([
        "chip_A_eco_v2", "chip_B_hotfix", "chip_F_test_opt",
        "chip_G_power_tuning", "chip_H_area_reduction",
    ]):
        create_version(base_time, 150 + i * 30, name, "RUNNING")

    # 5 FAIL versions
    for i, name in enumerate([
        "chip_I_experiment", "chip_J_aggressive", "chip_K_retry_v1",
        "chip_L_broken_floorplan", "chip_M_timing_fail",
    ]):
        create_version(base_time, 300 + i * 30, name, "FAIL")

    # 5 PENDING versions
    for i, name in enumerate([
        "chip_N_just_started", "chip_O_early_phase", "chip_P_waiting_queue",
        "chip_Q_new_branch", "chip_R_fresh_run",
    ]):
        create_version(base_time, 450 + i * 30, name, "PENDING")

    # 5 branch versions
    for i, name in enumerate([
        "chip_S_branched_cts", "chip_T_branched_route", "chip_U_branched_routeopt",
        "chip_AA_partial_flow", "chip_BB_eco_branch",
    ]):
        create_version(base_time, 600 + i * 30, name, "BRANCH")

    # 5 long-name stress versions
    for i, name in enumerate([
        "chip_X_ultra_aggressive_floorplan_experiment_v3_with_custom_clock_mesh_and_retention_islands",
        "chip_Y_multi_corner_multi_mode_optimization_run_with_advanced_power_gating_strategy_final",
        "chip_Z_experimental_3d_ic_integration_with_hybrid_bonding_and_through_silicon_via_analysis",
        "chip_W_low_power_iot_sensor_node_with_aggressive_voltage_scaling_and_adaptive_body_bias",
        "chip_V_high_performance_compute_tile_with_hbm3_memory_stack_and_custom_network_on_chip",
    ]):
        create_version(base_time, 750 + i * 30, name,
                       random.choice(["SUCCESS", "RUNNING", "FAIL"]))


def gen_suite2():
    """Suite 2: base 30 + 2 new versions + some status/runtime modifications."""
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    _gen_base_30()

    base_time = datetime.now()

    # Add 2 new versions
    create_version(base_time, 900, "chip_CC_new_arrival", "SUCCESS")
    create_version(base_time, 930, "chip_DD_latest_fix", "RUNNING")

    # Modify a few existing versions: change last SUCCESS step to RUNNING
    all_dirs = sorted(os.listdir(OUTPUT_DIR), reverse=True)
    for dir_name in all_dirs[:3]:
        dir_path = os.path.join(OUTPUT_DIR, dir_name)
        if not os.path.isdir(dir_path):
            continue
        step_files = sorted(
            [f for f in os.listdir(dir_path)
             if f.endswith(".json") and f != "run_info.json"],
            key=lambda x: STEP_NAMES.index(x.replace(".json", ""))
            if x.replace(".json", "") in STEP_NAMES else 99)
        for sf in reversed(step_files):
            sf_path = os.path.join(dir_path, sf)
            with open(sf_path, "r") as f:
                data = json.load(f)
            if data.get("status") == "SUCCESS":
                data["status"] = "RUNNING"
                if data.get("job"):
                    data["job"]["status"] = "RUNNING"
                    old = data["job"].get("runtime", "0m").rstrip("m") or "0"
                    data["job"]["runtime"] = str(int(old) + random.randint(5, 20)) + "m"
                with open(sf_path, "w") as f:
                    json.dump(data, f, indent=2)
                break

    sample_dirs = [os.path.join(OUTPUT_DIR, d) for d in sorted(os.listdir(OUTPUT_DIR))[:5]]
    create_sample_reports(sample_dirs)

    print(f"Suite 2: {len(os.listdir(OUTPUT_DIR))} versions")


def main():
    suite = "1"
    if len(sys.argv) > 1 and sys.argv[1] == "--suite":
        suite = sys.argv[2] if len(sys.argv) > 2 else "1"

    if suite == "2":
        gen_suite2()
        return

    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    _gen_base_30()

    # Create sample report files for the first 5 versions
    all_dirs = sorted(os.listdir(OUTPUT_DIR))
    sample_dirs = [os.path.join(OUTPUT_DIR, d) for d in all_dirs[:5]]
    create_sample_reports(sample_dirs)

    print(f"Generated test data in: {OUTPUT_DIR}")
    print(f"Total versions: {len(os.listdir(OUTPUT_DIR))}")


if __name__ == "__main__":
    main()
