import textwrap

from .downloader import Downloader


def assemble_metrics(downloader: Downloader) -> str:
    # count packages
    pkg_list = downloader.list_packages()
    pkg_done_count = sum(pkg["info"]["status"] == "done" for pkg in pkg_list)
    pkg_running_count = sum(pkg["info"]["status"] == "running" for pkg in pkg_list)
    pkg_queued_count = sum(pkg["info"]["status"] == "queued" for pkg in pkg_list)
    pkg_failed_count = sum(pkg["info"]["status"] == "failed" for pkg in pkg_list)
    pkg_unknown_count = sum(pkg["info"]["status"] == "unknown" for pkg in pkg_list)

    # retrieve server info
    info = downloader.get_server_info()
    du_total = info["disk_usage_raw"]["total"]
    du_used = info["disk_usage_raw"]["used"]
    process_memory = info["process"]["memory"]
    process_cpu = info["process"]["cpu"]

    # assemble response
    return textwrap.dedent(
        f"""\
        # HELP plyder_packages_total Number of downloads.
        # TYPE plyder_packages_total counter
        plyder_packages_total{{status="done"}} {pkg_done_count}
        plyder_packages_total{{status="running"}} {pkg_running_count}
        plyder_packages_total{{status="queued"}} {pkg_queued_count}
        plyder_packages_total{{status="failed"}} {pkg_failed_count}
        plyder_packages_total{{status="unknown"}} {pkg_unknown_count}
        # HELP plyder_disk_usage_bytes Disk usage.
        # TYPE plyder_disk_usage_bytes gauge
        plyder_disk_usage_bytes{{status="total"}} {du_total}
        plyder_disk_usage_bytes{{status="used"}} {du_used}
        # HELP plyder_process_memory Memory usage of plyder process.
        # TYPE plyder_process_memory gauge
        plyder_process_memory {process_memory}
        # HELP plyder_process_cpu CPU usage of plyder process.
        # TYPE plyder_process_cpu gauge
        plyder_process_cpu {process_cpu}
    """
    )
